import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import Calendar from '../components/Calendar'
import EventList from '../components/EventList'
import FeedForm from '../components/FeedForm'
import useEvents from '../hooks/useEvents'
import { api } from '../lib/api'

const AUTO_SYNC_STALE_MINUTES = 5

function monthRange(monthDate) {
  // Fetch a wide window so the Calendar grid AND the Upcoming list both have
  // data regardless of which month the user is currently viewing.
  // Calendar filters to its month client-side; EventList filters to next 14d.
  const first = new Date(monthDate.getFullYear(), monthDate.getMonth(), 1)
  const from = new Date(first)
  from.setDate(first.getDate() - 14) // show some recent past on the grid

  const now = new Date()
  const to = new Date(now)
  to.setDate(now.getDate() + 180) // always cover the next ~6 months of upcoming

  // Guarantee `to` is also after the displayed month's end
  const monthEnd = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 7)
  if (monthEnd > to) return { from: from.toISOString(), to: monthEnd.toISOString() }

  return { from: from.toISOString(), to: to.toISOString() }
}

export default function EventPage() {
  const [month, setMonth] = useState(() => new Date())
  const range = useMemo(() => monthRange(month), [month])
  const { events, loading, error, refetch, createEvent, deleteEvent } = useEvents({
    from: range.from,
    to: range.to,
  })
  const jumpedRef = useRef(false)

  // On first events load: if the current month is empty but there are future
  // events, jump forward to the month of the next upcoming event.
  useEffect(() => {
    if (jumpedRef.current) return
    if (!events.length) return
    const now = Date.now()
    const currentMonthStart = new Date(
      month.getFullYear(),
      month.getMonth(),
      1
    ).getTime()
    const currentMonthEnd = new Date(
      month.getFullYear(),
      month.getMonth() + 1,
      0,
      23,
      59,
      59
    ).getTime()
    const thisMonthHas = events.some((e) => {
      const t = new Date(e.start_date).getTime()
      return t >= currentMonthStart && t <= currentMonthEnd
    })
    if (thisMonthHas) {
      jumpedRef.current = true
      return
    }
    const nextFuture = events
      .filter((e) => new Date(e.start_date).getTime() >= now)
      .sort((a, b) => a.start_date.localeCompare(b.start_date))[0]
    if (nextFuture) {
      const d = new Date(nextFuture.start_date)
      setMonth(new Date(d.getFullYear(), d.getMonth(), 1))
      jumpedRef.current = true
    }
  }, [events, month])

  const [feeds, setFeeds] = useState(null)
  const [feedsLoading, setFeedsLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [syncResult, setSyncResult] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [pageError, setPageError] = useState(null)
  const autoSyncedRef = useRef(false)

  const loadFeeds = useCallback(async () => {
    setFeedsLoading(true)
    try {
      const f = await api.getFeeds()
      setFeeds(f)
      return f
    } finally {
      setFeedsLoading(false)
    }
  }, [])

  const runSync = useCallback(async () => {
    setSyncing(true)
    setPageError(null)
    try {
      const result = await api.postSync()
      setSyncResult(result)
      // update last_calendar_sync_at in UI
      setFeeds((prev) => ({
        ...(prev || {}),
        last_calendar_sync_at: result?.last_calendar_sync_at,
      }))
      await refetch()
      return result
    } catch (e) {
      setPageError(e?.message || 'Sync failed')
      throw e
    } finally {
      setSyncing(false)
    }
  }, [refetch])

  const saveFeeds = useCallback(
    async (body) => {
      setSaving(true)
      setPageError(null)
      try {
        const updated = await api.putFeeds(body)
        setFeeds(updated)
      } catch (e) {
        setPageError(e?.message || 'Failed to save feeds')
        throw e
      } finally {
        setSaving(false)
      }
    },
    []
  )

  // Live refresh when Sage (or any other client path) mutates the calendar.
  // Realtime voice dispatches this event after a successful create / cancel.
  useEffect(() => {
    const handler = () => {
      refetch().catch(() => {})
    }
    window.addEventListener('jarvis:calendar_changed', handler)
    return () => window.removeEventListener('jarvis:calendar_changed', handler)
  }, [refetch])

  // Initial load + auto-sync if stale
  useEffect(() => {
    let cancelled = false
    loadFeeds().then((f) => {
      if (cancelled || autoSyncedRef.current || !f) return
      const hasUrl = f.qut_timetable_ics_url || f.qut_canvas_ics_url
      if (!hasUrl) return

      const lastSync = f.last_calendar_sync_at
        ? new Date(f.last_calendar_sync_at).getTime()
        : 0
      const stale =
        Date.now() - lastSync > AUTO_SYNC_STALE_MINUTES * 60 * 1000
      if (stale) {
        autoSyncedRef.current = true
        runSync().catch(() => {})
      }
    })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const goPrev = () =>
    setMonth((m) => new Date(m.getFullYear(), m.getMonth() - 1, 1))
  const goNext = () =>
    setMonth((m) => new Date(m.getFullYear(), m.getMonth() + 1, 1))

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <header style={{ marginBottom: 20 }}>
        <div
          style={{
            fontFamily: 'monospace',
            fontSize: 11,
            letterSpacing: 3,
            color: 'rgba(0, 212, 255, 0.6)',
          }}
        >
          EVENT CONSOLE //
        </div>
        <h1 style={{ fontSize: 34, margin: 0, fontWeight: 700 }}>Your calendar</h1>
        <p
          style={{
            color: 'rgba(230, 246, 255, 0.6)',
            fontSize: 14,
            marginTop: 8,
            maxWidth: 680,
          }}
        >
          Connect your QUT Timetable and Canvas feeds. Jarvis will fetch every
          class and assignment due date and keep them in one place.
        </p>
      </header>

      {pageError && (
        <div
          style={{
            marginBottom: 16,
            padding: '10px 14px',
            borderRadius: 8,
            background: 'rgba(255, 80, 80, 0.1)',
            border: '1px solid rgba(255, 80, 80, 0.4)',
            color: 'rgba(255, 170, 170, 0.95)',
            fontSize: 13,
            fontFamily: 'monospace',
          }}
        >
          {pageError}
        </div>
      )}

      <div style={{ marginBottom: 24 }}>
        <FeedForm
          feeds={feedsLoading ? null : feeds}
          onSave={saveFeeds}
          onSync={runSync}
          saving={saving}
          syncing={syncing}
          lastSyncedAt={feeds?.last_calendar_sync_at}
        />
      </div>

      {syncResult && (
        <div
          style={{
            marginBottom: 24,
            padding: '12px 16px',
            borderRadius: 10,
            background: 'rgba(0, 212, 255, 0.06)',
            border: '1px solid rgba(0, 212, 255, 0.3)',
            fontSize: 13,
            color: 'rgba(230, 246, 255, 0.85)',
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            flexWrap: 'wrap',
          }}
        >
          <span
            style={{
              fontFamily: 'monospace',
              color: '#00d4ff',
              letterSpacing: 2,
            }}
          >
            SYNCED //
          </span>
          {Object.entries(syncResult.synced || {}).map(([src, count]) => (
            <span key={src}>
              <strong>{count}</strong> from <code>{src}</code>
            </span>
          ))}
          {(syncResult.errors || []).length > 0 && (
            <span style={{ color: 'rgba(255, 170, 170, 0.95)' }}>
              errors: {syncResult.errors.length}
            </span>
          )}
          <button
            type="button"
            onClick={() => setSyncResult(null)}
            style={{
              marginLeft: 'auto',
              background: 'transparent',
              border: '1px solid rgba(0, 212, 255, 0.3)',
              color: 'rgba(0, 212, 255, 0.7)',
              padding: '4px 10px',
              borderRadius: 6,
              cursor: 'pointer',
              fontFamily: 'monospace',
              fontSize: 11,
              letterSpacing: 1,
            }}
          >
            DISMISS
          </button>
        </div>
      )}

      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 24,
          alignItems: 'stretch',
        }}
      >
        <div>
          <Calendar
            month={month}
            events={events}
            onPrev={goPrev}
            onNext={goNext}
          />

          <div style={{ marginTop: 20 }}>
            <button
              type="button"
              onClick={() => setShowCreate((v) => !v)}
              style={{
                padding: '10px 16px',
                borderRadius: 8,
                border: '1px dashed rgba(0, 212, 255, 0.4)',
                background: 'rgba(0, 20, 40, 0.4)',
                color: '#00d4ff',
                fontFamily: 'monospace',
                fontSize: 12,
                letterSpacing: 2,
                cursor: 'pointer',
              }}
            >
              {showCreate ? '− HIDE MANUAL EVENT' : '+ NEW MANUAL EVENT'}
            </button>
            {showCreate && (
              <ManualEventForm
                onCreate={async (body) => {
                  await createEvent(body)
                  setShowCreate(false)
                }}
              />
            )}
          </div>

          {loading && (
            <div
              style={{
                marginTop: 12,
                fontSize: 12,
                color: 'rgba(0, 212, 255, 0.55)',
                fontFamily: 'monospace',
              }}
            >
              loading events…
            </div>
          )}
          {error && (
            <div
              style={{
                marginTop: 12,
                fontSize: 12,
                color: 'rgba(255, 170, 170, 0.95)',
                fontFamily: 'monospace',
              }}
            >
              {error}
            </div>
          )}
        </div>
        <EventList events={events} onDelete={deleteEvent} />
      </div>
    </div>
  )
}

function ManualEventForm({ onCreate }) {
  const [title, setTitle] = useState('')
  const [date, setDate] = useState('')
  const [startTime, setStartTime] = useState('09:00')
  const [endTime, setEndTime] = useState('10:00')
  const [location, setLocation] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    if (!title || !date) {
      setError('Title and date are required.')
      return
    }
    const start = new Date(`${date}T${startTime}:00`)
    const end = new Date(`${date}T${endTime}:00`)
    if (Number.isNaN(start.getTime())) {
      setError('Invalid date/time.')
      return
    }
    setBusy(true)
    try {
      await onCreate({
        title,
        start_date: start.toISOString(),
        end_date: Number.isNaN(end.getTime()) ? null : end.toISOString(),
        location: location || null,
        event_type: 'event',
      })
      setTitle('')
      setDate('')
      setLocation('')
    } catch (e2) {
      setError(e2?.message || 'Create failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form
      onSubmit={submit}
      style={{
        marginTop: 14,
        padding: 16,
        borderRadius: 10,
        background: 'rgba(0, 20, 40, 0.55)',
        border: '1px solid rgba(0, 212, 255, 0.25)',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
        gap: 10,
        alignItems: 'end',
      }}
    >
      <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <span style={manualLabel}>TITLE</span>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          style={manualInput}
          placeholder="Study group"
        />
      </label>
      <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <span style={manualLabel}>DATE</span>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          style={manualInput}
        />
      </label>
      <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <span style={manualLabel}>START</span>
        <input
          type="time"
          value={startTime}
          onChange={(e) => setStartTime(e.target.value)}
          style={manualInput}
        />
      </label>
      <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <span style={manualLabel}>END</span>
        <input
          type="time"
          value={endTime}
          onChange={(e) => setEndTime(e.target.value)}
          style={manualInput}
        />
      </label>
      <label
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 4,
          gridColumn: '1 / -1',
        }}
      >
        <span style={manualLabel}>LOCATION (optional)</span>
        <input
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          style={manualInput}
          placeholder="Library L4"
        />
      </label>
      {error && (
        <div
          style={{
            gridColumn: '1 / -1',
            color: 'rgba(255, 170, 170, 0.95)',
            fontSize: 12,
            fontFamily: 'monospace',
          }}
        >
          {error}
        </div>
      )}
      <button
        type="submit"
        disabled={busy}
        style={{
          padding: '10px 14px',
          borderRadius: 8,
          border: '1px solid rgba(0, 212, 255, 0.65)',
          background: 'rgba(0, 212, 255, 0.18)',
          color: '#00d4ff',
          fontFamily: 'monospace',
          fontSize: 12,
          letterSpacing: 2,
          cursor: 'pointer',
          gridColumn: '1 / -1',
        }}
      >
        {busy ? 'CREATING…' : 'CREATE EVENT'}
      </button>
    </form>
  )
}

const manualLabel = {
  fontFamily: 'monospace',
  fontSize: 10,
  letterSpacing: 2,
  color: 'rgba(0, 212, 255, 0.55)',
}

const manualInput = {
  padding: '9px 11px',
  borderRadius: 6,
  border: '1px solid rgba(0, 212, 255, 0.25)',
  background: 'rgba(0, 10, 25, 0.65)',
  color: '#e6f6ff',
  fontSize: 13,
  fontFamily: 'monospace',
  outline: 'none',
}
