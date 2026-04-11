import { useEffect, useState } from 'react'

export default function FeedForm({
  feeds,
  onSave,
  onSync,
  saving,
  syncing,
  lastSyncedAt,
}) {
  const [timetable, setTimetable] = useState('')
  const [canvas, setCanvas] = useState('')
  const [error, setError] = useState(null)
  const [justSaved, setJustSaved] = useState(false)

  useEffect(() => {
    setTimetable(feeds?.qut_timetable_ics_url || '')
    setCanvas(feeds?.qut_canvas_ics_url || '')
  }, [feeds])

  const validate = () => {
    setError(null)
    for (const [label, value] of [
      ['QUT Timetable URL', timetable],
      ['QUT Canvas URL', canvas],
    ]) {
      if (!value) continue
      if (!value.startsWith('https://')) {
        setError(`${label} must start with https://`)
        return false
      }
    }
    return true
  }

  const handleSave = async (e) => {
    e?.preventDefault?.()
    if (!validate()) return
    await onSave({
      qut_timetable_ics_url: timetable || '',
      qut_canvas_ics_url: canvas || '',
    })
    setJustSaved(true)
    setTimeout(() => setJustSaved(false), 2000)
  }

  const handleSync = async () => {
    setError(null)
    try {
      await onSync()
    } catch (e) {
      setError(e?.message || 'Sync failed')
    }
  }

  return (
    <form
      onSubmit={handleSave}
      style={{
        background: 'rgba(0, 20, 40, 0.55)',
        border: '1px solid rgba(0, 212, 255, 0.25)',
        borderRadius: 14,
        padding: 20,
        display: 'flex',
        flexDirection: 'column',
        gap: 14,
      }}
    >
      <div>
        <div
          style={{
            fontFamily: 'monospace',
            fontSize: 11,
            letterSpacing: 3,
            color: 'rgba(0, 212, 255, 0.6)',
          }}
        >
          CALENDAR FEEDS //
        </div>
        <div style={{ fontSize: 18, fontWeight: 600, marginTop: 2 }}>
          Connect QUT Timetable & Canvas
        </div>
        <div
          style={{
            fontSize: 12,
            color: 'rgba(230, 246, 255, 0.55)',
            marginTop: 4,
          }}
        >
          Paste the ICS subscription URLs from{' '}
          <code>mytimetable.qut.edu.au</code> and <code>canvas.qut.edu.au</code>.
          Jarvis will keep them in sync.
        </div>
      </div>

      <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <span style={labelStyle}>QUT TIMETABLE ICS URL</span>
        <input
          type="url"
          value={timetable}
          onChange={(e) => setTimetable(e.target.value)}
          placeholder="https://mytimetable.qut.edu.au/aplus/rest/calendar/ical/…"
          style={inputStyle}
        />
      </label>
      <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <span style={labelStyle}>QUT CANVAS ICS URL</span>
        <input
          type="url"
          value={canvas}
          onChange={(e) => setCanvas(e.target.value)}
          placeholder="https://canvas.qut.edu.au/feeds/calendars/user_….ics"
          style={inputStyle}
        />
      </label>

      {error && (
        <div
          style={{
            padding: '8px 10px',
            borderRadius: 6,
            background: 'rgba(255, 80, 80, 0.1)',
            border: '1px solid rgba(255, 80, 80, 0.35)',
            color: 'rgba(255, 170, 170, 0.95)',
            fontSize: 12,
            fontFamily: 'monospace',
          }}
        >
          {error}
        </div>
      )}

      <div
        style={{
          display: 'flex',
          gap: 10,
          alignItems: 'center',
          flexWrap: 'wrap',
        }}
      >
        <button
          type="submit"
          disabled={saving}
          style={{
            ...primaryBtn,
            opacity: saving ? 0.6 : 1,
          }}
        >
          {saving ? 'SAVING…' : justSaved ? 'SAVED ✓' : 'SAVE'}
        </button>
        <button
          type="button"
          onClick={handleSync}
          disabled={syncing}
          style={{
            ...secondaryBtn,
            opacity: syncing ? 0.6 : 1,
          }}
        >
          {syncing ? 'SYNCING…' : 'SYNC NOW'}
        </button>
        {lastSyncedAt && (
          <div
            style={{
              fontSize: 11,
              color: 'rgba(0, 212, 255, 0.6)',
              fontFamily: 'monospace',
              marginLeft: 'auto',
            }}
          >
            last sync: {new Date(lastSyncedAt).toLocaleString()}
          </div>
        )}
      </div>
    </form>
  )
}

const labelStyle = {
  fontSize: 11,
  letterSpacing: 2,
  fontFamily: 'monospace',
  color: 'rgba(0, 212, 255, 0.55)',
}

const inputStyle = {
  padding: '10px 12px',
  borderRadius: 8,
  border: '1px solid rgba(0, 212, 255, 0.25)',
  background: 'rgba(0, 10, 25, 0.65)',
  color: '#e6f6ff',
  fontSize: 13,
  fontFamily: 'monospace',
  outline: 'none',
}

const primaryBtn = {
  padding: '10px 18px',
  borderRadius: 8,
  border: '1px solid rgba(0, 212, 255, 0.65)',
  background: 'rgba(0, 212, 255, 0.18)',
  color: '#00d4ff',
  fontFamily: 'monospace',
  fontSize: 12,
  letterSpacing: 2,
  cursor: 'pointer',
  fontWeight: 600,
}

const secondaryBtn = {
  padding: '10px 18px',
  borderRadius: 8,
  border: '1px solid rgba(255, 149, 0, 0.55)',
  background: 'rgba(255, 149, 0, 0.12)',
  color: '#ff9500',
  fontFamily: 'monospace',
  fontSize: 12,
  letterSpacing: 2,
  cursor: 'pointer',
  fontWeight: 600,
}
