/**
 * useRealtime — OpenAI Realtime API client via WebRTC.
 *
 * Flow:
 *   1. POST /api/realtime/session     → backend calls OpenAI to mint a short-lived client_secret
 *   2. Create RTCPeerConnection       → add mic track, expect remote audio track
 *   3. Create SDP offer               → POST https://api.openai.com/v1/realtime?model=... with Authorization: Bearer <client_secret>
 *   4. Receive SDP answer             → setRemoteDescription, connection is live
 *   5. Open a data channel            → send/receive JSON events (conversation.item.create, etc.)
 *
 * Audio:
 *   - Mic track is automatically captured & encoded by the browser (Opus over SRTP).
 *   - The assistant's audio arrives as an incoming track and is routed into
 *     a dynamically-created <audio autoplay> element attached to document.body.
 *
 * This hook does NOT touch JarvisCanvas / useVoice / useJarvis. Import it
 * into whichever component wants Realtime and call `connect()`.
 *
 * Example:
 *   const { isConnected, connect, disconnect, sendEvent } = useRealtime()
 *   useEffect(() => { connect() }, [])   // or gate behind a button click
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { supabase } from '../lib/supabase'

const SESSION_ENDPOINT = '/api/realtime/session'
const DEBUG_ENDPOINT = '/api/realtime/debug'
// GA endpoint (Oct 2025+). The beta `/v1/realtime` path rejects GA client
// secrets (ek_*) with `api_version_mismatch`.
const OPENAI_REALTIME_URL = 'https://api.openai.com/v1/realtime/calls'

// Generate a short session tag so we can correlate breadcrumbs with a
// specific connection attempt in the server-side debug log.
function newSessionTag() {
  return Math.random().toString(36).slice(2, 10)
}

// Canonical UUID pattern (8-4-4-4-12 hex).
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

/**
 * Resolve a free-form subject reference to a canonical UUID.
 *
 * Sage (OpenAI Realtime) occasionally truncates long opaque strings when it
 * echoes them back as tool-call arguments — the 36-char UUID `36097dbe-763a-...`
 * becomes just `36097dbe`. If we forward that to `/api/subjects/:id` Postgres
 * will reject the short string as an invalid UUID and return a 500. This
 * helper runs BEFORE the fetch so we never send garbage to the server:
 *
 *   1. Full UUID → return as-is if it matches one of the user's subjects.
 *   2. UUID prefix (6+ hex chars) → match against subject.id startsWith.
 *      If exactly one subject matches, use it.
 *   3. Exact code (case-insensitive) → match against subject.code.
 *   4. Exact name (case-insensitive) → match against subject.name.
 *   5. Substring on code or name → first match wins.
 *
 * Returns the full UUID of the matching subject, or null.
 *
 * @param {Array<{id: string, name?: string, code?: string}>} subjects - from GET /api/subjects
 * @param {string} ref - user-provided or model-echoed reference
 * @returns {string | null}
 */
function resolveSubjectRef(subjects, ref) {
  if (!Array.isArray(subjects) || !subjects.length) return null
  const raw = String(ref || '').trim()
  if (!raw) return null
  const lower = raw.toLowerCase()

  // 1. Full UUID
  if (UUID_RE.test(raw)) {
    const hit = subjects.find((s) => (s.id || '').toLowerCase() === lower)
    return hit ? hit.id : null
  }

  // 2. UUID prefix (hex-only, 6+ chars, dashes allowed)
  const hexOnly = lower.replace(/-/g, '')
  if (hexOnly.length >= 6 && /^[0-9a-f]+$/.test(hexOnly)) {
    const prefixMatches = subjects.filter((s) =>
      (s.id || '').toLowerCase().startsWith(lower)
    )
    if (prefixMatches.length === 1) return prefixMatches[0].id
    // 2+ matches → ambiguous, fall through to name/code checks
  }

  // 3. Exact code
  const exactCode = subjects.find(
    (s) => (s.code || '').trim().toLowerCase() === lower
  )
  if (exactCode) return exactCode.id

  // 4. Exact name
  const exactName = subjects.find(
    (s) => (s.name || '').trim().toLowerCase() === lower
  )
  if (exactName) return exactName.id

  // 5. Substring
  const sub = subjects.find(
    (s) =>
      (s.code || '').toLowerCase().includes(lower) ||
      (s.name || '').toLowerCase().includes(lower)
  )
  return sub ? sub.id : null
}

// Fire-and-forget debug breadcrumb to the backend so we can tail client
// state from the server. Swallows all errors — debug must not affect flow.
function postDebug(sessionTag, event, data) {
  try {
    fetch(DEBUG_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event, session: sessionTag, data: data || {} }),
      keepalive: true,
    }).catch(() => {})
  } catch {
    // ignore
  }
}

// Add a default end_date of start + 1h when the model omits it. OpenAI usually
// provides one, but we guard against missing values so the backend doesn't
// have to.
function ensureEndDate(args) {
  if (!args || typeof args !== 'object') return args
  if (args.end_date || !args.start_date) return args
  try {
    const start = new Date(args.start_date)
    if (Number.isNaN(start.getTime())) return args
    const end = new Date(start.getTime() + 60 * 60 * 1000)
    // Preserve the original timezone offset suffix if present, otherwise
    // fall back to ISO string.
    return { ...args, end_date: end.toISOString() }
  } catch {
    return args
  }
}

/**
 * Execute a function call that came from the Realtime data channel by
 * routing it to the appropriate /api/admin endpoint. Returns a JSON-safe
 * object that we pass back to OpenAI as function_call_output.
 */
async function executeRealtimeTool(sessionTag, name, rawArgs) {
  let args = {}
  try {
    args = typeof rawArgs === 'string' ? JSON.parse(rawArgs) : rawArgs || {}
  } catch {
    return { error: 'bad_arguments_json', raw: String(rawArgs).slice(0, 200) }
  }

  const { data: sessionData } = await supabase.auth.getSession()
  const token = sessionData?.session?.access_token
  if (!token) {
    return { error: 'not_signed_in', message: 'User must sign in on the admin panel first.' }
  }
  const auth = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }

  postDebug(sessionTag, 'tool_call_start', { name, args })

  try {
    if (name === 'create_event') {
      const body = ensureEndDate({
        title: args.title,
        start_date: args.start_date,
        end_date: args.end_date,
        description: args.description,
        location: args.location,
      })
      const res = await fetch('/api/admin/events', {
        method: 'POST',
        headers: auth,
        body: JSON.stringify(body),
      })
      const data = await res.json().catch(() => ({}))
      postDebug(sessionTag, 'tool_call_result', {
        name,
        status: res.status,
        id: data?.id || null,
      })
      if (!res.ok) {
        return { error: 'create_failed', status: res.status, detail: data?.detail || null }
      }
      // Tell the UI to refetch if the user is on /event.
      window.dispatchEvent(
        new CustomEvent('jarvis:calendar_changed', { detail: { action: 'create', event: data } })
      )
      return {
        status: 'created',
        id: data?.id,
        title: data?.title,
        start_date: data?.start_date,
        end_date: data?.end_date,
        location: data?.location,
      }
    }

    if (name === 'get_upcoming_events') {
      const days = Math.max(1, Math.min(30, Number(args.days) || 7))
      const now = new Date()
      const to = new Date(now.getTime() + days * 86_400_000)
      const qs = new URLSearchParams({ from: now.toISOString(), to: to.toISOString() }).toString()
      const res = await fetch(`/api/admin/events?${qs}`, { headers: auth })
      const data = await res.json().catch(() => ({}))
      postDebug(sessionTag, 'tool_call_result', {
        name,
        status: res.status,
        count: (data?.events || []).length,
      })
      if (!res.ok) {
        return { error: 'fetch_failed', status: res.status }
      }
      const events = (data?.events || []).slice(0, 30).map((e) => ({
        id: e.id,
        title: e.title,
        start_date: e.start_date,
        end_date: e.end_date,
        location: e.location,
        source: e.source,
      }))
      return { count: events.length, events }
    }

    if (name === 'cancel_event') {
      const id = args.event_id
      if (!id) return { error: 'missing_event_id' }
      const res = await fetch(`/api/admin/events/${encodeURIComponent(id)}`, {
        method: 'DELETE',
        headers: auth,
      })
      postDebug(sessionTag, 'tool_call_result', { name, status: res.status, id })
      if (!res.ok) return { error: 'delete_failed', status: res.status }
      window.dispatchEvent(
        new CustomEvent('jarvis:calendar_changed', { detail: { action: 'delete', id } })
      )
      return { status: 'deleted', id }
    }

    // -------- Meal & Friends --------
    if (name === 'list_eateries') {
      const params = new URLSearchParams()
      if (args.cuisine) params.set('cuisine', args.cuisine)
      if (args.trending_only) params.set('trending_only', 'true')
      if (args.limit) params.set('limit', String(args.limit))
      const qs = params.toString()
      const res = await fetch(`/api/meal-buddy/eateries${qs ? `?${qs}` : ''}`, { headers: auth })
      if (!res.ok) return { error: 'list_failed', status: res.status }
      const data = await res.json()
      return { count: (data.eateries || []).length, eateries: (data.eateries || []).slice(0, 15) }
    }

    if (name === 'get_meal_preferences') {
      const res = await fetch('/api/meal-buddy/preferences', { headers: auth })
      if (!res.ok) return { error: 'fetch_failed', status: res.status }
      return await res.json()
    }

    if (name === 'update_meal_preferences') {
      const res = await fetch('/api/meal-buddy/preferences', {
        method: 'PUT',
        headers: auth,
        body: JSON.stringify(args),
      })
      if (!res.ok) return { error: 'update_failed', status: res.status }
      window.dispatchEvent(new CustomEvent('jarvis:meal_buddy_changed', { detail: { part: 'preferences' } }))
      return await res.json()
    }

    if (name === 'add_meal_pick') {
      let eateryId = args.eatery_id
      if (!eateryId && args.eatery_name) {
        // Resolve by name via the list endpoint
        const listRes = await fetch(`/api/meal-buddy/eateries?limit=200`, { headers: auth })
        if (listRes.ok) {
          const listBody = await listRes.json()
          const match = (listBody.eateries || []).find(
            (e) => e.name.toLowerCase().includes(args.eatery_name.toLowerCase())
          )
          if (match) eateryId = match.id
        }
      }
      if (!eateryId) return { error: 'eatery_not_found' }
      const res = await fetch('/api/meal-buddy/picks', {
        method: 'POST',
        headers: auth,
        body: JSON.stringify({ eatery_id: eateryId }),
      })
      if (!res.ok) {
        const body = await res.text()
        return { error: 'add_failed', status: res.status, detail: body.slice(0, 200) }
      }
      window.dispatchEvent(new CustomEvent('jarvis:meal_buddy_changed', { detail: { part: 'picks' } }))
      return { status: 'added', eatery_id: eateryId }
    }

    if (name === 'set_dining_availability') {
      const res = await fetch('/api/meal-buddy/availability', {
        method: 'PUT',
        headers: auth,
        body: JSON.stringify(args),
      })
      if (!res.ok) return { error: 'set_failed', status: res.status }
      window.dispatchEvent(new CustomEvent('jarvis:meal_buddy_changed', { detail: { part: 'availability' } }))
      return { status: 'set', ...args }
    }

    if (name === 'list_meal_matches') {
      const qs = args.status ? `?status=${encodeURIComponent(args.status)}` : ''
      const res = await fetch(`/api/meal-buddy/matches${qs}`, { headers: auth })
      if (!res.ok) return { error: 'fetch_failed', status: res.status }
      const data = await res.json()
      return { count: (data.matches || []).length, matches: data.matches || [] }
    }

    if (name === 'get_meal_picks') {
      const res = await fetch('/api/meal-buddy/picks', { headers: auth })
      if (!res.ok) return { error: 'fetch_failed', status: res.status }
      return await res.json()
    }

    if (name === 'remove_meal_pick') {
      let eateryId = args.eatery_id
      if (!eateryId && args.eatery_name) {
        // Resolve by name via the user's current picks (name match)
        const listRes = await fetch('/api/meal-buddy/picks', { headers: auth })
        if (listRes.ok) {
          const listBody = await listRes.json()
          const match = (listBody.picks || []).find(
            (p) => p.eateries?.name?.toLowerCase().includes(args.eatery_name.toLowerCase())
          )
          if (match) eateryId = match.eatery_id
        }
      }
      if (!eateryId) return { error: 'pick_not_found' }
      const res = await fetch(`/api/meal-buddy/picks/${encodeURIComponent(eateryId)}`, {
        method: 'DELETE',
        headers: auth,
      })
      if (!res.ok) return { error: 'remove_failed', status: res.status }
      window.dispatchEvent(new CustomEvent('jarvis:meal_buddy_changed', { detail: { part: 'picks' } }))
      return { status: 'removed', eatery_id: eateryId }
    }

    if (name === 'clear_dining_availability') {
      const qs = new URLSearchParams({
        slot_date: args.slot_date,
        slot_time: args.slot_time,
      }).toString()
      const res = await fetch(`/api/meal-buddy/availability?${qs}`, {
        method: 'DELETE',
        headers: auth,
      })
      if (!res.ok) return { error: 'clear_failed', status: res.status }
      window.dispatchEvent(new CustomEvent('jarvis:meal_buddy_changed', { detail: { part: 'availability' } }))
      return { status: 'cleared', ...args }
    }

    if (name === 'list_other_users_for_match') {
      const res = await fetch('/api/meal-buddy/users', { headers: auth })
      if (!res.ok) return { error: 'fetch_failed', status: res.status }
      return await res.json()
    }

    if (name === 'propose_meal_match') {
      const res = await fetch('/api/meal-buddy/matches', {
        method: 'POST',
        headers: auth,
        body: JSON.stringify({
          other_user_id: args.other_user_id,
          eatery_id: args.eatery_id,
          scheduled_at: args.scheduled_at,
          meal_type: args.meal_type,
        }),
      })
      if (!res.ok) {
        const text = await res.text()
        return { error: 'propose_failed', status: res.status, detail: text.slice(0, 200) }
      }
      const data = await res.json()
      window.dispatchEvent(new CustomEvent('jarvis:meal_buddy_changed', { detail: { part: 'matches' } }))
      return data
    }

    if (name === 'respond_to_meal_match') {
      const res = await fetch(
        `/api/meal-buddy/matches/${encodeURIComponent(args.match_id)}/respond`,
        {
          method: 'POST',
          headers: auth,
          body: JSON.stringify({ response: args.response }),
        }
      )
      if (!res.ok) return { error: 'respond_failed', status: res.status }
      window.dispatchEvent(new CustomEvent('jarvis:meal_buddy_changed', { detail: { part: 'matches' } }))
      return await res.json()
    }

    // -------- Subjects / course helper --------
    if (name === 'list_subjects') {
      const res = await fetch('/api/subjects', { headers: auth })
      if (!res.ok) return { error: 'fetch_failed', status: res.status }
      const data = await res.json()
      return { count: (data.subjects || []).length, subjects: data.subjects || [] }
    }

    if (name === 'get_subject_context') {
      // Sage (OpenAI Realtime) sometimes truncates opaque UUIDs when echoing
      // them back as tool args — e.g. passing "36097dbe" instead of the full
      // "36097dbe-763a-4cac-9e09-925add560fd4". Resolve any short/malformed
      // ref against the canonical subject list BEFORE hitting /api/subjects/:id,
      // which expects a real UUID. The backend ALSO has a fallback now, but
      // this avoids the round-trip and cleaner logs on the happy path.
      const candidate = args.subject_id || args.subject_name || ''
      const ref = String(candidate).trim()
      if (!ref) return { error: 'subject_not_found', reason: 'no ref provided' }

      const listRes = await fetch('/api/subjects', { headers: auth })
      if (!listRes.ok) return { error: 'list_failed', status: listRes.status }
      const listBody = await listRes.json()
      const allSubjects = listBody.subjects || []
      const sid = resolveSubjectRef(allSubjects, ref)
      if (!sid) return { error: 'subject_not_found', ref }

      // The detail endpoint returns {subject, materials} — assemble a compact dossier for Sage
      const detRes = await fetch(`/api/subjects/${encodeURIComponent(sid)}`, { headers: auth })
      if (!detRes.ok) return { error: 'fetch_failed', status: detRes.status }
      const detail = await detRes.json()
      const subj = detail.subject || {}
      const mats = (detail.materials || []).map((m) => ({
        kind: m.kind,
        title: m.title || m.file_name,
        snippet: (m.content_text || '').slice(0, 500),
      }))
      return {
        subject_id: sid,
        name: subj.name,
        code: subj.code,
        term: subj.term,
        description: subj.description,
        materials_count: mats.length,
        materials: mats,
      }
    }

    if (name === 'search_subject_materials') {
      const q = (args.query || '').toLowerCase().trim()
      if (!q) return { error: 'empty_query' }
      const limit = Math.max(1, Math.min(Number(args.limit) || 5, 15))

      // Frontend-side search: fetch all subjects (scoped optionally), scan
      // their materials' content_text for the query, return top N snippets.
      const listRes = await fetch('/api/subjects', { headers: auth })
      if (!listRes.ok) return { error: 'list_failed', status: listRes.status }
      const listBody = await listRes.json()
      let subjects = listBody.subjects || []
      if (args.subject_name) {
        const ref = args.subject_name.toLowerCase()
        subjects = subjects.filter(
          (s) =>
            (s.name || '').toLowerCase().includes(ref) ||
            (s.code || '').toLowerCase().includes(ref)
        )
      }

      const matches = []
      for (const s of subjects) {
        if (matches.length >= limit) break
        const detRes = await fetch(`/api/subjects/${encodeURIComponent(s.id)}`, { headers: auth })
        if (!detRes.ok) continue
        const det = await detRes.json()
        for (const m of det.materials || []) {
          const content = m.content_text || ''
          const idx = content.toLowerCase().indexOf(q)
          if (idx === -1) continue
          const start = Math.max(0, idx - 120)
          const end = Math.min(content.length, idx + q.length + 240)
          let snippet = content.slice(start, end).replace(/\n/g, ' ')
          if (start > 0) snippet = '…' + snippet
          if (end < content.length) snippet = snippet + '…'
          matches.push({
            subject_id: s.id,
            subject_name: s.name,
            subject_code: s.code,
            kind: m.kind,
            title: m.title || m.file_name,
            snippet,
          })
          if (matches.length >= limit) break
        }
      }
      return { count: matches.length, matches }
    }

    if (name === 'create_subject') {
      if (!args.name) return { error: 'missing_name' }
      const res = await fetch('/api/subjects', {
        method: 'POST',
        headers: auth,
        body: JSON.stringify({
          name: args.name,
          code: args.code,
          term: args.term,
          description: args.description,
        }),
      })
      if (!res.ok) return { error: 'create_failed', status: res.status }
      window.dispatchEvent(new CustomEvent('jarvis:subjects_changed', { detail: { action: 'create' } }))
      return await res.json()
    }

    if (name === 'add_subject_material_text') {
      // Same truncation defense as get_subject_context above.
      const candidate = args.subject_id || args.subject_name || ''
      const ref = String(candidate).trim()
      if (!ref) return { error: 'subject_not_found', reason: 'no ref provided' }
      const listRes = await fetch('/api/subjects', { headers: auth })
      if (!listRes.ok) return { error: 'list_failed', status: listRes.status }
      const listBody = await listRes.json()
      const sid = resolveSubjectRef(listBody.subjects || [], ref)
      if (!sid) return { error: 'subject_not_found', ref }
      if (!args.kind || !args.content_text) return { error: 'missing_kind_or_content' }
      const res = await fetch(`/api/subjects/${encodeURIComponent(sid)}/materials/text`, {
        method: 'POST',
        headers: auth,
        body: JSON.stringify({
          kind: args.kind,
          title: args.title,
          content_text: args.content_text,
        }),
      })
      if (!res.ok) return { error: 'add_failed', status: res.status }
      const created = await res.json()
      window.dispatchEvent(new CustomEvent('jarvis:subjects_changed', { detail: { action: 'add_material', subject_id: sid } }))
      return { status: 'added', material_id: created.id, subject_id: sid, kind: args.kind }
    }

    return { error: 'unknown_tool', name }
  } catch (err) {
    postDebug(sessionTag, 'tool_call_exception', {
      name,
      message: err?.message || String(err),
    })
    return { error: 'tool_exception', message: err?.message || String(err) }
  }
}

export default function useRealtime() {
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState(null)
  const [sessionInfo, setSessionInfo] = useState(null)
  const [isAssistantSpeaking, setIsAssistantSpeaking] = useState(false)

  const pcRef = useRef(null)
  const audioElRef = useRef(null)
  const dataChannelRef = useRef(null)
  const localStreamRef = useRef(null)

  // Ensure a single <audio> element for the assistant's voice output.
  const getAudioEl = useCallback(() => {
    if (audioElRef.current) return audioElRef.current
    const el = document.createElement('audio')
    el.autoplay = true
    el.setAttribute('data-jarvis-realtime-audio', 'true')
    // Hidden; we only care about playback.
    el.style.display = 'none'
    document.body.appendChild(el)
    audioElRef.current = el
    return el
  }, [])

  const cleanup = useCallback(() => {
    try {
      dataChannelRef.current?.close()
    } catch {
      // ignore
    }
    dataChannelRef.current = null

    try {
      localStreamRef.current?.getTracks().forEach((t) => t.stop())
    } catch {
      // ignore
    }
    localStreamRef.current = null

    try {
      pcRef.current?.close()
    } catch {
      // ignore
    }
    pcRef.current = null

    if (audioElRef.current) {
      try {
        audioElRef.current.srcObject = null
      } catch {
        // ignore
      }
    }

    setIsConnected(false)
    setIsAssistantSpeaking(false)
  }, [])

  const sendEvent = useCallback((event) => {
    const dc = dataChannelRef.current
    if (!dc || dc.readyState !== 'open') {
      console.warn('[realtime] data channel not open, cannot send', event)
      return false
    }
    try {
      dc.send(JSON.stringify(event))
      return true
    } catch (e) {
      console.error('[realtime] sendEvent failed', e)
      return false
    }
  }, [])

  const connect = useCallback(async () => {
    if (isConnecting || isConnected) return
    setError(null)
    setIsConnecting(true)

    const sessionTag = newSessionTag()
    postDebug(sessionTag, 'connect_start', {
      ua: navigator.userAgent.slice(0, 120),
      hasRTCPC: typeof RTCPeerConnection === 'function',
      hasGUM: !!navigator.mediaDevices?.getUserMedia,
    })

    try {
      // 1. Ask backend for a client secret. Forward the Supabase JWT so the
      // backend can inject a personalized meal-buddy dossier into Sage's
      // session instructions at mint time.
      postDebug(sessionTag, 'session_post_start')
      const {
        data: { session: authSession },
      } = await supabase.auth.getSession()
      const sessionHeaders = { 'Content-Type': 'application/json' }
      if (authSession?.access_token) {
        sessionHeaders.Authorization = `Bearer ${authSession.access_token}`
      }
      const tokenRes = await fetch(SESSION_ENDPOINT, {
        method: 'POST',
        headers: sessionHeaders,
        body: '{}',
      })
      if (!tokenRes.ok) {
        const body = await tokenRes.text()
        postDebug(sessionTag, 'session_post_err', { status: tokenRes.status, body: body.slice(0, 200) })
        throw new Error(`Session endpoint ${tokenRes.status}: ${body}`)
      }
      const token = await tokenRes.json()
      if (!token?.client_secret) {
        postDebug(sessionTag, 'session_post_no_secret', { got: Object.keys(token || {}) })
        throw new Error('Session endpoint returned no client_secret')
      }
      postDebug(sessionTag, 'session_post_ok', {
        model: token.model,
        voice: token.voice,
        expiresAt: token.expires_at,
      })
      setSessionInfo(token)

      // 2. Peer connection + remote audio sink.
      const pc = new RTCPeerConnection()
      pcRef.current = pc
      postDebug(sessionTag, 'pc_created')

      const audioEl = getAudioEl()
      pc.ontrack = (event) => {
        postDebug(sessionTag, 'pc_ontrack', {
          kind: event.track?.kind,
          streams: event.streams?.length || 0,
          trackMuted: event.track?.muted,
          readyState: event.track?.readyState,
        })
        if (event.streams && event.streams[0]) {
          audioEl.srcObject = event.streams[0]
          // Browsers sometimes block autoplay of audio from peer connections.
          // Try to play explicitly and log the outcome.
          const playPromise = audioEl.play?.()
          if (playPromise?.then) {
            playPromise
              .then(() => postDebug(sessionTag, 'remote_audio_play_ok'))
              .catch((err) =>
                postDebug(sessionTag, 'remote_audio_play_blocked', {
                  name: err?.name,
                  message: err?.message,
                })
              )
          }
        }
      }

      // 3. Data channel for JSON control / transcript events.
      const dc = pc.createDataChannel('oai-events')
      dataChannelRef.current = dc
      dc.onopen = () => {
        postDebug(sessionTag, 'dc_open')
      }
      dc.onmessage = (evt) => {
        let msg
        try {
          msg = JSON.parse(evt.data)
        } catch {
          return
        }
        // Forward interesting event types as breadcrumbs so the server-side
        // log shows what OpenAI is saying back. Skip the high-volume delta
        // spam (audio.delta fires many times per response) but signal their
        // first occurrence for a given response.
        const t = msg.type
        if (
          t === 'session.created' ||
          t === 'session.updated' ||
          t === 'input_audio_buffer.speech_started' ||
          t === 'input_audio_buffer.speech_stopped' ||
          t === 'input_audio_buffer.committed' ||
          t === 'conversation.item.created' ||
          t === 'response.created' ||
          t === 'response.done' ||
          t === 'response.output_audio.done' ||
          t === 'response.output_audio_transcript.done' ||
          t === 'response.function_call_arguments.done' ||
          t === 'error'
        ) {
          postDebug(sessionTag, `oai_${t}`, {
            itemType: msg.item?.type,
            role: msg.item?.role,
            name: msg.name,
            call_id: msg.call_id,
            transcript: msg.transcript?.slice?.(0, 120),
            err: msg.error?.message,
          })
        }
        // Tool / function-call handling — this is the new piece that gives
        // Sage real hands on the calendar.
        if (t === 'response.function_call_arguments.done') {
          const callId = msg.call_id
          const name = msg.name
          const rawArgs = msg.arguments
          ;(async () => {
            const result = await executeRealtimeTool(sessionTag, name, rawArgs)
            // Send the output back into the conversation so the model can
            // acknowledge / speak a confirmation.
            try {
              dataChannelRef.current?.send(
                JSON.stringify({
                  type: 'conversation.item.create',
                  item: {
                    type: 'function_call_output',
                    call_id: callId,
                    output: JSON.stringify(result),
                  },
                })
              )
              dataChannelRef.current?.send(
                JSON.stringify({ type: 'response.create' })
              )
              postDebug(sessionTag, 'tool_output_sent', { name, call_id: callId })
            } catch (err) {
              postDebug(sessionTag, 'tool_output_send_err', {
                name,
                message: err?.message || String(err),
              })
            }
          })()
        }
        // Coarse UX signal: is the assistant currently speaking?
        if (t === 'response.audio.delta' || t === 'response.output_audio.delta') {
          setIsAssistantSpeaking(true)
        } else if (
          t === 'response.audio.done' ||
          t === 'response.output_audio.done' ||
          t === 'response.done'
        ) {
          setIsAssistantSpeaking(false)
        } else if (t === 'error') {
          // eslint-disable-next-line no-console
          console.error('[realtime] error event', msg)
        }
      }
      dc.onclose = () => {
        postDebug(sessionTag, 'dc_close')
      }
      dc.onerror = (err) => {
        postDebug(sessionTag, 'dc_error', { message: err?.message || 'unknown' })
      }

      // 4. Pick a real physical mic (avoid virtual loopback drivers like
      // BlackHole, Soundflower, Loopback.app, Aggregate devices, etc. — those
      // have no physical input and will feed OpenAI a stream of silence).
      // Then capture it and attach to the peer connection.
      let preferredDeviceId = null
      let preferredLabel = null
      try {
        const devices = await navigator.mediaDevices.enumerateDevices()
        const audioInputs = devices.filter((d) => d.kind === 'audioinput')
        const virtualRegex =
          /blackhole|loopback|soundflower|virtual|aggregate|multi-?output|iShowU|rogue amoeba|vb-audio|voicemeeter|obs/i
        // Prefer a device whose label does NOT match known virtual drivers.
        // Fall back to `default`, then the first available.
        const physical = audioInputs.find(
          (d) => d.label && !virtualRegex.test(d.label)
        )
        const fallback =
          audioInputs.find((d) => d.deviceId === 'default') ||
          audioInputs[0] ||
          null
        const chosen = physical || fallback
        if (chosen) {
          preferredDeviceId = chosen.deviceId
          preferredLabel = chosen.label || '(unnamed)'
        }
        postDebug(sessionTag, 'enumerate_devices', {
          total: audioInputs.length,
          labels: audioInputs.map((d) => (d.label || '').slice(0, 60)),
          chosen: preferredLabel,
        })
      } catch (err) {
        postDebug(sessionTag, 'enumerate_devices_err', {
          message: err?.message || String(err),
        })
      }

      postDebug(sessionTag, 'gum_start', { requestedDevice: preferredLabel })
      let stream
      try {
        const constraints = preferredDeviceId
          ? {
              audio: {
                deviceId: { exact: preferredDeviceId },
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
              },
            }
          : { audio: true }
        stream = await navigator.mediaDevices.getUserMedia(constraints)
      } catch (gumErr) {
        postDebug(sessionTag, 'gum_err', {
          name: gumErr?.name,
          message: gumErr?.message,
          constraintType: preferredDeviceId ? 'deviceId' : 'default',
        })
        // If the exact deviceId constraint failed, retry with default as a
        // safety net (some edge cases around deviceId changing between
        // enumerate and gUM calls).
        if (preferredDeviceId) {
          try {
            stream = await navigator.mediaDevices.getUserMedia({ audio: true })
            postDebug(sessionTag, 'gum_fallback_ok')
          } catch (retryErr) {
            postDebug(sessionTag, 'gum_fallback_err', {
              name: retryErr?.name,
              message: retryErr?.message,
            })
            throw retryErr
          }
        } else {
          throw gumErr
        }
      }
      localStreamRef.current = stream
      const tracks = stream.getAudioTracks()
      postDebug(sessionTag, 'gum_ok', {
        trackCount: tracks.length,
        label: tracks[0]?.label || null,
        enabled: tracks[0]?.enabled,
        muted: tracks[0]?.muted,
      })
      tracks.forEach((track) => pc.addTrack(track, stream))

      // 5. SDP offer/answer via OpenAI's Realtime endpoint.
      const offer = await pc.createOffer()
      await pc.setLocalDescription(offer)
      postDebug(sessionTag, 'sdp_offer_ready', { bytes: offer.sdp?.length })

      const sdpRes = await fetch(
        `${OPENAI_REALTIME_URL}?model=${encodeURIComponent(token.model)}`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token.client_secret}`,
            'Content-Type': 'application/sdp',
          },
          body: offer.sdp,
        }
      )
      postDebug(sessionTag, 'sdp_post_response', {
        status: sdpRes.status,
        ok: sdpRes.ok,
      })
      if (!sdpRes.ok) {
        const body = await sdpRes.text()
        postDebug(sessionTag, 'sdp_post_err_body', { body: body.slice(0, 300) })
        throw new Error(`OpenAI SDP ${sdpRes.status}: ${body}`)
      }
      const answerSdp = await sdpRes.text()
      await pc.setRemoteDescription({ type: 'answer', sdp: answerSdp })
      postDebug(sessionTag, 'sdp_answer_set', { bytes: answerSdp.length })

      pc.onconnectionstatechange = () => {
        postDebug(sessionTag, 'pc_state', {
          state: pc.connectionState,
          ice: pc.iceConnectionState,
        })
        if (
          pc.connectionState === 'disconnected' ||
          pc.connectionState === 'failed' ||
          pc.connectionState === 'closed'
        ) {
          cleanup()
        }
      }
      pc.oniceconnectionstatechange = () => {
        postDebug(sessionTag, 'ice_state', { state: pc.iceConnectionState })
      }

      setIsConnected(true)
      postDebug(sessionTag, 'connect_complete')
    } catch (e) {
      postDebug(sessionTag, 'connect_failed', {
        name: e?.name,
        message: e?.message || String(e),
      })
      // eslint-disable-next-line no-console
      console.error('[realtime] connect failed', e)
      setError(e?.message || String(e))
      cleanup()
    } finally {
      setIsConnecting(false)
    }
  }, [isConnecting, isConnected, cleanup, getAudioEl])

  const disconnect = useCallback(() => {
    cleanup()
    setSessionInfo(null)
  }, [cleanup])

  // Teardown on unmount.
  useEffect(() => {
    return () => {
      cleanup()
      if (audioElRef.current) {
        try {
          audioElRef.current.remove()
        } catch {
          // ignore
        }
        audioElRef.current = null
      }
    }
  }, [cleanup])

  return {
    isConnected,
    isConnecting,
    isAssistantSpeaking,
    error,
    sessionInfo,
    connect,
    disconnect,
    sendEvent,
  }
}
