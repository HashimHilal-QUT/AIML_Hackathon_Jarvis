function groupByDay(events) {
  const groups = new Map()
  for (const ev of events) {
    if (!ev.start_date) continue
    const d = new Date(ev.start_date)
    if (Number.isNaN(d.getTime())) continue
    const key = d.toLocaleDateString(undefined, {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
    })
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key).push(ev)
  }
  return [...groups.entries()]
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const SOURCE_LABEL = {
  qut_timetable: 'QUT',
  qut_canvas: 'CANVAS',
  outlook: 'OUTLOOK',
  google: 'GOOGLE',
  manual: 'MANUAL',
}

export default function EventList({ events = [], onDelete }) {
  if (!events.length) {
    return (
      <div
        style={{
          padding: 24,
          borderRadius: 14,
          background: 'rgba(0, 20, 40, 0.4)',
          border: '1px dashed rgba(0, 212, 255, 0.25)',
          color: 'rgba(230, 246, 255, 0.55)',
          fontSize: 13,
          textAlign: 'center',
        }}
      >
        No upcoming events. Paste your QUT URLs above and hit <em>Sync Now</em>.
      </div>
    )
  }

  const upcoming = events
    .filter((e) => {
      if (!e.start_date) return false
      return new Date(e.start_date).getTime() >= Date.now() - 1000 * 60 * 60
    })
    .slice(0, 40)

  const grouped = groupByDay(upcoming)

  return (
    <div
      style={{
        background: 'rgba(0, 20, 40, 0.55)',
        border: '1px solid rgba(0, 212, 255, 0.25)',
        borderRadius: 14,
        overflow: 'hidden',
      }}
    >
      <header
        style={{
          padding: '16px 20px',
          background: 'rgba(0, 30, 60, 0.55)',
          borderBottom: '1px solid rgba(0, 212, 255, 0.18)',
        }}
      >
        <div
          style={{
            fontFamily: 'monospace',
            fontSize: 11,
            letterSpacing: 3,
            color: 'rgba(0, 212, 255, 0.55)',
          }}
        >
          UPCOMING //
        </div>
        <div style={{ fontSize: 18, fontWeight: 600, marginTop: 2 }}>
          Next 14 days
        </div>
      </header>

      <div style={{ maxHeight: 520, overflowY: 'auto' }}>
        {grouped.map(([day, list]) => (
          <div key={day}>
            <div
              style={{
                padding: '8px 20px',
                fontFamily: 'monospace',
                fontSize: 11,
                letterSpacing: 2,
                color: 'rgba(0, 212, 255, 0.6)',
                background: 'rgba(0, 15, 30, 0.6)',
                borderBottom: '1px solid rgba(0, 212, 255, 0.12)',
                position: 'sticky',
                top: 0,
                zIndex: 1,
              }}
            >
              {day.toUpperCase()}
            </div>
            {list.map((ev) => (
              <div
                key={ev.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '10px 20px',
                  borderBottom: '1px solid rgba(0, 212, 255, 0.06)',
                  borderLeft: `3px solid ${ev.color || '#534AB7'}`,
                }}
              >
                <div
                  style={{
                    minWidth: 60,
                    fontFamily: 'monospace',
                    fontSize: 12,
                    color: 'rgba(0, 212, 255, 0.75)',
                  }}
                >
                  {formatTime(ev.start_date)}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>
                    {ev.title}
                  </div>
                  <div
                    style={{
                      fontSize: 11,
                      color: 'rgba(230, 246, 255, 0.55)',
                      marginTop: 2,
                      display: 'flex',
                      gap: 8,
                    }}
                  >
                    {ev.location && <span>📍 {ev.location}</span>}
                    <span
                      style={{
                        color: ev.color || 'rgba(0, 212, 255, 0.55)',
                        fontFamily: 'monospace',
                        letterSpacing: 1,
                      }}
                    >
                      [{SOURCE_LABEL[ev.source] || ev.source}]
                    </span>
                  </div>
                </div>
                {onDelete && (
                  <button
                    type="button"
                    onClick={() => onDelete(ev.id)}
                    title="Delete event"
                    style={{
                      background: 'transparent',
                      border: '1px solid rgba(255, 80, 80, 0.3)',
                      color: 'rgba(255, 120, 120, 0.8)',
                      borderRadius: 6,
                      padding: '4px 8px',
                      fontSize: 11,
                      cursor: 'pointer',
                      fontFamily: 'monospace',
                    }}
                  >
                    DEL
                  </button>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
