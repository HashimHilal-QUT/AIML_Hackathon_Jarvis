import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'
import MealBuddyNav from '../components/MealBuddyNav'
import MealBuddySetupBanner from '../components/MealBuddySetupBanner'

const TIME_SLOTS = [
  { code: '1130', label: '11:30 AM', defaultMeal: 'lunch' },
  { code: '1230', label: '12:30 PM', defaultMeal: 'lunch' },
  { code: '1800', label: '6:00 PM', defaultMeal: 'dinner' },
  { code: '1900', label: '7:00 PM', defaultMeal: 'dinner' },
]

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function addDays(date, n) {
  const d = new Date(date)
  d.setDate(d.getDate() + n)
  return d
}

function ymd(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export default function AvailabilityPage() {
  // Week starting from Monday of the current week
  const weekStart = useMemo(() => {
    const today = new Date()
    const jsDow = today.getDay() // 0 = Sun
    const offset = (jsDow + 6) % 7 // 0 = Mon ... 6 = Sun
    const monday = new Date(today)
    monday.setDate(today.getDate() - offset)
    return monday
  }, [])

  const days = useMemo(
    () => Array.from({ length: 7 }, (_, i) => addDays(weekStart, i)),
    [weekStart]
  )

  const [availability, setAvailability] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [setupInfo, setSetupInfo] = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    setSetupInfo(null)
    try {
      const from = ymd(days[0])
      const to = ymd(days[6])
      const res = await api.getAvailability(from, to)
      setAvailability(res.availability || [])
    } catch (e) {
      if (e?.status === 412 && e?.structured?.error === 'schema_not_ready') {
        setSetupInfo(e.structured)
      } else {
        setError(e?.message || 'Failed to load availability')
      }
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    refresh()
  }, [refresh])

  const slotMap = useMemo(() => {
    const map = new Map()
    for (const a of availability) {
      map.set(`${a.slot_date}|${a.slot_time}`, a.meal_type)
    }
    return map
  }, [availability])

  const cycleSlot = async (date, slot) => {
    const key = `${date}|${slot.code}`
    const current = slotMap.get(key)
    try {
      if (!current) {
        await api.setAvailability({
          slot_date: date,
          slot_time: slot.code,
          meal_type: slot.defaultMeal,
        })
      } else if (current === 'lunch') {
        await api.setAvailability({
          slot_date: date,
          slot_time: slot.code,
          meal_type: 'dinner',
        })
      } else {
        await api.clearAvailability(date, slot.code)
      }
      await refresh()
    } catch (e) {
      alert(e?.message || 'Update failed')
    }
  }

  if (setupInfo) {
    return (
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <MealBuddyNav />
        <MealBuddySetupBanner info={setupInfo} onRetry={refresh} />
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto' }}>
      <MealBuddyNav />
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 32, margin: 0, fontWeight: 700 }}>When are we eating?</h1>
        <p
          style={{
            color: 'rgba(230, 246, 255, 0.6)',
            fontSize: 14,
            marginTop: 8,
            maxWidth: 620,
          }}
        >
          Click a slot to cycle through <span style={{ color: '#f5a623' }}>LUNCH</span> →{' '}
          <span style={{ color: '#00d4ff' }}>DINNER</span> → cleared. Jarvis will use
          overlapping slots to suggest meal matches.
        </p>
      </header>

      {error && <div style={errorBox}>{error}</div>}
      {loading && (
        <div
          style={{
            color: 'rgba(230, 246, 255, 0.5)',
            fontFamily: 'monospace',
            fontSize: 12,
            marginBottom: 10,
          }}
        >
          loading…
        </div>
      )}

      <div
        style={{
          padding: 20,
          borderRadius: 12,
          background: 'rgba(0, 20, 40, 0.6)',
          border: '1px solid rgba(0, 212, 255, 0.25)',
          overflowX: 'auto',
        }}
      >
        {/* Day header row */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '90px repeat(7, minmax(0, 1fr))',
            gap: 4,
            marginBottom: 12,
            paddingBottom: 12,
            borderBottom: '1px solid rgba(0, 212, 255, 0.15)',
          }}
        >
          <div />
          {days.map((d, i) => (
            <div key={i} style={{ textAlign: 'center' }}>
              <div
                style={{
                  fontFamily: 'monospace',
                  fontSize: 10,
                  color: 'rgba(230, 246, 255, 0.5)',
                  letterSpacing: 1,
                }}
              >
                {DAY_LABELS[i].toUpperCase()}
              </div>
              <div
                style={{
                  fontFamily: 'monospace',
                  fontSize: 18,
                  color: '#e6f6ff',
                  fontWeight: 600,
                }}
              >
                {d.getDate()}
              </div>
            </div>
          ))}
        </div>

        {/* Time rows */}
        {TIME_SLOTS.map((slot) => (
          <div
            key={slot.code}
            style={{
              display: 'grid',
              gridTemplateColumns: '90px repeat(7, minmax(0, 1fr))',
              gap: 4,
              marginBottom: 4,
            }}
          >
            <div
              style={{
                fontFamily: 'monospace',
                fontSize: 10,
                color: 'rgba(230, 246, 255, 0.45)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-end',
                paddingRight: 10,
              }}
            >
              {slot.label}
            </div>
            {days.map((d) => {
              const date = ymd(d)
              const type = slotMap.get(`${date}|${slot.code}`)
              return (
                <button
                  key={date}
                  type="button"
                  onClick={() => cycleSlot(date, slot)}
                  style={{
                    height: 56,
                    borderRadius: 6,
                    border:
                      type === 'lunch'
                        ? '1px solid #f5a623'
                        : type === 'dinner'
                          ? '1px solid #00d4ff'
                          : '1px solid rgba(0, 212, 255, 0.12)',
                    background:
                      type === 'lunch'
                        ? 'rgba(245, 166, 35, 0.12)'
                        : type === 'dinner'
                          ? 'rgba(0, 100, 180, 0.2)'
                          : 'rgba(6, 24, 40, 0.6)',
                    color:
                      type === 'lunch'
                        ? '#f5a623'
                        : type === 'dinner'
                          ? '#00d4ff'
                          : 'transparent',
                    fontFamily: 'monospace',
                    fontSize: 10,
                    fontWeight: 600,
                    letterSpacing: 1,
                    textTransform: 'uppercase',
                    cursor: 'pointer',
                    boxShadow: type ? `0 0 8px ${type === 'lunch' ? 'rgba(245,166,35,0.15)' : 'rgba(0,200,255,0.15)'}` : 'none',
                  }}
                >
                  {type || ''}
                </button>
              )
            })}
          </div>
        ))}
      </div>

      <div
        style={{
          marginTop: 16,
          display: 'flex',
          gap: 16,
          fontFamily: 'monospace',
          fontSize: 10,
          color: 'rgba(230, 246, 255, 0.55)',
        }}
      >
        <span>
          <span
            style={{
              display: 'inline-block',
              width: 12,
              height: 12,
              marginRight: 6,
              background: 'rgba(245, 166, 35, 0.12)',
              border: '1px solid #f5a623',
              verticalAlign: 'middle',
            }}
          />
          LUNCH
        </span>
        <span>
          <span
            style={{
              display: 'inline-block',
              width: 12,
              height: 12,
              marginRight: 6,
              background: 'rgba(0, 100, 180, 0.2)',
              border: '1px solid #00d4ff',
              verticalAlign: 'middle',
            }}
          />
          DINNER
        </span>
        <span style={{ marginLeft: 'auto' }}>
          Tap a slot to cycle: empty → lunch → dinner → empty
        </span>
      </div>
    </div>
  )
}

const errorBox = {
  padding: '10px 14px',
  borderRadius: 8,
  background: 'rgba(255, 80, 80, 0.1)',
  border: '1px solid rgba(255, 80, 80, 0.4)',
  color: 'rgba(255, 170, 170, 0.95)',
  fontSize: 12,
  fontFamily: 'monospace',
  marginBottom: 16,
}
