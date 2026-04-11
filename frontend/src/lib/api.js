import { supabase } from './supabase'

// Vite proxy forwards /api -> http://localhost:8000 and STRIPS the /api prefix,
// so /api/admin/feeds arrives at the backend as /admin/feeds (which matches
// the admin router's prefix). Keep using /api/admin/* here so the call site
// looks normal.
const BASE = '/api'

async function authedFetch(path, options = {}) {
  const {
    data: { session },
  } = await supabase.auth.getSession()

  const headers = {
    ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    ...(session?.access_token
      ? { Authorization: `Bearer ${session.access_token}` }
      : {}),
    ...(options.headers || {}),
  }

  const response = await fetch(`${BASE}${path}`, {
    ...options,
    headers,
  })

  if (response.status === 401) {
    // Session is dead — let the AuthProvider re-check.
    window.dispatchEvent(new CustomEvent('auth:invalid'))
  }

  if (!response.ok) {
    let detail = response.statusText
    let body = null
    try {
      body = await response.json()
      detail = typeof body.detail === 'string' ? body.detail : body.detail?.message || detail
    } catch {
      // ignore
    }
    const err = new Error(`[${response.status}] ${detail}`)
    err.status = response.status
    err.body = body
    // For structured errors (FastAPI wraps body in {detail: {...}}), surface the inner object
    if (body && typeof body.detail === 'object' && body.detail !== null) {
      err.structured = body.detail
    }
    throw err
  }

  if (response.status === 204) return null
  const ct = response.headers.get('content-type') || ''
  return ct.includes('application/json') ? response.json() : response.text()
}

async function authedFetchMultipart(path, formData) {
  const {
    data: { session },
  } = await supabase.auth.getSession()
  const headers = {}
  if (session?.access_token) {
    headers.Authorization = `Bearer ${session.access_token}`
  }
  const response = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers,
    body: formData,
  })
  if (!response.ok) {
    let detail = response.statusText
    try {
      const errBody = await response.json()
      detail = errBody.detail || detail
    } catch {
      /* ignore */
    }
    throw new Error(`[${response.status}] ${detail}`)
  }
  return response.json()
}

export const api = {
  getFeeds: () => authedFetch('/admin/feeds'),
  putFeeds: (body) =>
    authedFetch('/admin/feeds', {
      method: 'PUT',
      body: JSON.stringify(body),
    }),
  postSync: () => authedFetch('/admin/sync', { method: 'POST' }),
  getEvents: ({ from, to } = {}) => {
    const params = new URLSearchParams()
    if (from) params.set('from', from)
    if (to) params.set('to', to)
    const qs = params.toString()
    return authedFetch(`/admin/events${qs ? `?${qs}` : ''}`)
  },
  postEvent: (body) =>
    authedFetch('/admin/events', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  deleteEvent: (id) =>
    authedFetch(`/admin/events/${id}`, { method: 'DELETE' }),

  // -------- Subjects --------
  listSubjects: () => authedFetch('/subjects'),
  createSubject: (body) =>
    authedFetch('/subjects', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  getSubject: (id) => authedFetch(`/subjects/${id}`),
  updateSubject: (id, body) =>
    authedFetch(`/subjects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(body),
    }),
  deleteSubject: (id) =>
    authedFetch(`/subjects/${id}`, { method: 'DELETE' }),

  // Material CRUD (text + file)
  createMaterialText: (subjectId, body) =>
    authedFetch(`/subjects/${subjectId}/materials/text`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  uploadMaterialFile: (subjectId, { file, kind, title, hint }) => {
    const form = new FormData()
    form.append('file', file)
    form.append('kind', kind)
    if (title) form.append('title', title)
    if (hint) form.append('hint', hint)
    return authedFetchMultipart(`/subjects/${subjectId}/materials/upload`, form)
  },
  listMaterials: (subjectId, kind) => {
    const qs = kind ? `?kind=${encodeURIComponent(kind)}` : ''
    return authedFetch(`/subjects/${subjectId}/materials${qs}`)
  },
  deleteMaterial: (subjectId, materialId) =>
    authedFetch(`/subjects/${subjectId}/materials/${materialId}`, {
      method: 'DELETE',
    }),

  // -------- Meal & Friends --------
  getDiningPrefs: () => authedFetch('/meal-buddy/preferences'),
  putDiningPrefs: (body) =>
    authedFetch('/meal-buddy/preferences', {
      method: 'PUT',
      body: JSON.stringify(body),
    }),
  listEateries: (params = {}) => {
    const qs = new URLSearchParams()
    if (params.cuisine) qs.set('cuisine', params.cuisine)
    if (params.trending_only) qs.set('trending_only', 'true')
    if (params.limit) qs.set('limit', String(params.limit))
    const str = qs.toString()
    return authedFetch(`/meal-buddy/eateries${str ? `?${str}` : ''}`)
  },
  getEatery: (id) => authedFetch(`/meal-buddy/eateries/${id}`),
  getPicks: () => authedFetch('/meal-buddy/picks'),
  addPick: (eatery_id) =>
    authedFetch('/meal-buddy/picks', {
      method: 'POST',
      body: JSON.stringify({ eatery_id }),
    }),
  removePick: (eatery_id) =>
    authedFetch(`/meal-buddy/picks/${eatery_id}`, { method: 'DELETE' }),
  getAvailability: (from, to) => {
    const qs = new URLSearchParams()
    if (from) qs.set('from', from)
    if (to) qs.set('to', to)
    const str = qs.toString()
    return authedFetch(`/meal-buddy/availability${str ? `?${str}` : ''}`)
  },
  setAvailability: (body) =>
    authedFetch('/meal-buddy/availability', {
      method: 'PUT',
      body: JSON.stringify(body),
    }),
  clearAvailability: (slot_date, slot_time) => {
    const qs = new URLSearchParams({ slot_date, slot_time }).toString()
    return authedFetch(`/meal-buddy/availability?${qs}`, { method: 'DELETE' })
  },
  listMatches: (status) => {
    const qs = status ? `?status=${encodeURIComponent(status)}` : ''
    return authedFetch(`/meal-buddy/matches${qs}`)
  },
  proposeMatch: (body) =>
    authedFetch('/meal-buddy/matches', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  respondMatch: (match_id, response) =>
    authedFetch(`/meal-buddy/matches/${match_id}/respond`, {
      method: 'POST',
      body: JSON.stringify({ response }),
    }),
  getDiningStats: () => authedFetch('/meal-buddy/stats'),
  listOtherUsers: () => authedFetch('/meal-buddy/users'),
}
