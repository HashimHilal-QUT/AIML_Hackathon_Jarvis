import { useMemo, useState } from 'react'

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function startOfMonth(d) {
  return new Date(d.getFullYear(), d.getMonth(), 1)
}

function toLocalKey(iso) {
  if (!iso) return null
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

/**
 * Pure presentational month-view calendar.
 * Props:
 *   month:    Date (any day in the month to display)
 *   events:   [{id, title, start_date, end_date, event_type, color, source, ...}]
 *   onPrev, onNext: callbacks for month nav
 *   onEventClick:   optional callback(event)
 */
export default function Calendar({ month, events = [], onPrev, onNext, onEventClick }) {
  const [activeDay, setActiveDay] = useState(null)

  const { days, monthLabel } = useMemo(() => buildGrid(month), [month])
  const eventsByDay = useMemo(() => {
    const map = new Map()
    for (const ev of events) {
      const key = toLocalKey(ev.start_date)
      if (!key) continue
      if (!map.has(key)) map.set(key, [])
      map.get(key).push(ev)
    }
    // Sort each day's events by start time
    for (const [, list] of map) {
      list.sort((a, b) => (a.start_date || '').localeCompare(b.start_date || ''))
    }
    return map
  }, [events])

  const todayKey = toLocalKey(new Date().toISOString())
  const activeDayEvents = activeDay ? eventsByDay.get(activeDay) || [] : []

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
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 20px',
          background: 'rgba(0, 30, 60, 0.55)',
          borderBottom: '1px solid rgba(0, 212, 255, 0.18)',
        }}
      >
        <div>
          <div
            style={{
              fontFamily: 'monospace',
              fontSize: 11,
              letterSpacing: 3,
              color: 'rgba(0, 212, 255, 0.55)',
            }}
          >
            CALENDAR //
          </div>
          <div style={{ fontSize: 22, fontWeight: 700, marginTop: 2 }}>
            {monthLabel}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button type="button" onClick={onPrev} style={navBtn}>
            ◀
          </button>
          <button
            type="button"
            onClick={() => onNext && onPrev && onPrev(new Date()) /* handled by parent */}
            style={{ ...navBtn, display: 'none' }}
          >
            today
          </button>
          <button type="button" onClick={onNext} style={navBtn}>
            ▶
          </button>
        </div>
      </header>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(7, minmax(0, 1fr))',
          borderBottom: '1px solid rgba(0, 212, 255, 0.12)',
        }}
      >
        {DAY_LABELS.map((l) => (
          <div
            key={l}
            style={{
              padding: '10px 8px',
              textAlign: 'center',
              fontFamily: 'monospace',
              fontSize: 11,
              letterSpacing: 2,
              color: 'rgba(0, 212, 255, 0.55)',
              background: 'rgba(0, 30, 60, 0.3)',
            }}
          >
            {l}
          </div>
        ))}
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(7, minmax(0, 1fr))',
          gridAutoRows: 'minmax(100px, auto)',
        }}
      >
        {days.map((d) => {
          const key = d.key
          const dayEvents = eventsByDay.get(key) || []
          const inMonth = d.inMonth
          const isToday = key === todayKey
          return (
            <div
              key={key}
              onClick={() => setActiveDay(key)}
              style={{
                padding: 6,
                borderRight: '1px solid rgba(0, 212, 255, 0.08)',
                borderBottom: '1px solid rgba(0, 212, 255, 0.08)',
                background: inMonth
                  ? 'rgba(0, 10, 20, 0.3)'
                  : 'rgba(0, 5, 12, 0.45)',
                opacity: inMonth ? 1 : 0.4,
                cursor: 'pointer',
                position: 'relative',
                minHeight: 100,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  fontSize: 12,
                  fontFamily: 'monospace',
                  color: isToday ? '#00d4ff' : 'rgba(230, 246, 255, 0.65)',
                  fontWeight: isToday ? 700 : 500,
                }}
              >
                <span
                  style={
                    isToday
                      ? {
                          background: 'rgba(0, 212, 255, 0.2)',
                          border: '1px solid rgba(0, 212, 255, 0.6)',
                          borderRadius: 4,
                          padding: '1px 6px',
                        }
                      : undefined
                  }
                >
                  {d.day}
                </span>
                {dayEvents.length > 0 && (
                  <span
                    style={{
                      fontSize: 10,
                      color: 'rgba(0, 212, 255, 0.5)',
                    }}
                  >
                    {dayEvents.length}
                  </span>
                )}
              </div>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 3,
                  marginTop: 4,
                }}
              >
                {dayEvents.slice(0, 3).map((ev) => (
                  <button
                    key={ev.id}
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation()
                      onEventClick?.(ev)
                    }}
                    title={`${ev.title} @ ${formatTime(ev.start_date)}`}
                    style={{
                      display: 'block',
                      textAlign: 'left',
                      width: '100%',
                      padding: '3px 6px',
                      borderRadius: 4,
                      border: 'none',
                      background: (ev.color || '#534AB7') + '40',
                      borderLeft: `2px solid ${ev.color || '#534AB7'}`,
                      color: '#e6f6ff',
                      fontSize: 11,
                      overflow: 'hidden',
                      whiteSpace: 'nowrap',
                      textOverflow: 'ellipsis',
                      cursor: 'pointer',
                    }}
                  >
                    {formatTime(ev.start_date) && (
                      <span
                        style={{
                          opacity: 0.65,
                          marginRight: 4,
                          fontFamily: 'monospace',
                          fontSize: 10,
                        }}
                      >
                        {formatTime(ev.start_date)}
                      </span>
                    )}
                    {ev.title}
                  </button>
                ))}
                {dayEvents.length > 3 && (
                  <div
                    style={{
                      fontSize: 10,
                      color: 'rgba(0, 212, 255, 0.6)',
                      fontFamily: 'monospace',
                      paddingLeft: 4,
                    }}
                  >
                    +{dayEvents.length - 3} more
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {activeDay && activeDayEvents.length > 0 && (
        <div
          style={{
            borderTop: '1px solid rgba(0, 212, 255, 0.2)',
            background: 'rgba(0, 30, 60, 0.4)',
            padding: '12px 16px',
          }}
        >
          <div
            style={{
              fontFamily: 'monospace',
              fontSize: 11,
              letterSpacing: 2,
              color: 'rgba(0, 212, 255, 0.6)',
              marginBottom: 8,
            }}
          >
            {activeDay} //
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {activeDayEvents.map((ev) => (
              <div
                key={ev.id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '6px 8px',
                  borderRadius: 6,
                  background: 'rgba(0, 10, 20, 0.55)',
                  borderLeft: `3px solid ${ev.color || '#534AB7'}`,
                }}
              >
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{ev.title}</div>
                  {ev.location && (
                    <div
                      style={{
                        fontSize: 11,
                        color: 'rgba(230, 246, 255, 0.55)',
                      }}
                    >
                      📍 {ev.location}
                    </div>
                  )}
                </div>
                <div
                  style={{
                    fontSize: 11,
                    fontFamily: 'monospace',
                    color: 'rgba(0, 212, 255, 0.7)',
                  }}
                >
                  {formatTime(ev.start_date)}
                  {ev.end_date ? ` – ${formatTime(ev.end_date)}` : ''}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function buildGrid(referenceDate) {
  const ref = referenceDate || new Date()
  const first = startOfMonth(ref)
  const monthLabel = ref.toLocaleDateString(undefined, {
    month: 'long',
    year: 'numeric',
  })

  // Start grid on Monday of the week containing day 1
  const jsDow = first.getDay() // 0 = Sun
  const offset = (jsDow + 6) % 7 // 0 = Mon ... 6 = Sun
  const gridStart = new Date(first)
  gridStart.setDate(first.getDate() - offset)

  const days = []
  for (let i = 0; i < 42; i++) {
    const d = new Date(gridStart)
    d.setDate(gridStart.getDate() + i)
    days.push({
      date: d,
      day: d.getDate(),
      inMonth: d.getMonth() === ref.getMonth(),
      key: toLocalKey(d.toISOString()),
    })
  }
  return { days, monthLabel }
}

const navBtn = {
  width: 34,
  height: 34,
  borderRadius: 8,
  border: '1px solid rgba(0, 212, 255, 0.3)',
  background: 'rgba(0, 20, 40, 0.4)',
  color: '#00d4ff',
  fontSize: 14,
  cursor: 'pointer',
  fontFamily: 'monospace',
}
