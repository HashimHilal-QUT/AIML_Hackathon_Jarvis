import { useCallback, useEffect, useState } from 'react'
import { api } from '../lib/api'
import MealBuddyNav from '../components/MealBuddyNav'
import MealBuddySetupBanner from '../components/MealBuddySetupBanner'

const STATUS_COLORS = {
  proposed: '#f5a623',
  accepted: '#7fffa0',
  declined: 'rgba(255, 120, 120, 0.8)',
  completed: '#00d4ff',
  cancelled: 'rgba(230, 246, 255, 0.4)',
}

export default function MatchesPage() {
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [setupInfo, setSetupInfo] = useState(null)
  const [showProposer, setShowProposer] = useState(false)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    setSetupInfo(null)
    try {
      const res = await api.listMatches()
      setMatches(res.matches || [])
    } catch (e) {
      if (e?.status === 412 && e?.structured?.error === 'schema_not_ready') {
        setSetupInfo(e.structured)
      } else {
        setError(e?.message || 'Failed to load matches')
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const handleRespond = async (matchId, response) => {
    try {
      await api.respondMatch(matchId, response)
      await refresh()
    } catch (e) {
      alert(e?.message || 'Response failed')
    }
  }

  if (setupInfo) {
    return (
      <div style={{ maxWidth: 1000, margin: '0 auto' }}>
        <MealBuddyNav />
        <MealBuddySetupBanner info={setupInfo} onRetry={refresh} />
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <MealBuddyNav />
      <header
        style={{
          marginBottom: 24,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
        }}
      >
        <div>
          <h1 style={{ fontSize: 32, margin: 0, fontWeight: 700 }}>Dining proposals</h1>
          <p
            style={{
              color: 'rgba(230, 246, 255, 0.6)',
              fontSize: 14,
              marginTop: 8,
              maxWidth: 560,
            }}
          >
            Every proposed, accepted, or completed match with another student.
            Ask Jarvis to propose a new one, or use the button below.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowProposer(true)}
          style={primaryBtn}
        >
          + PROPOSE MATCH
        </button>
      </header>

      {error && <div style={errorBox}>{error}</div>}

      {loading && !matches.length && (
        <div style={{ fontFamily: 'monospace', color: 'rgba(230, 246, 255, 0.5)' }}>
          Loading…
        </div>
      )}

      {!matches.length && !loading && (
        <div style={emptyBox}>
          No matches yet. Use <strong>+ PROPOSE MATCH</strong> or ask Jarvis:
          <em> "Propose a lunch match with [email] at Sushi Zen tomorrow 12:30 pm"</em>.
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {matches.map((m) => (
          <MatchCard key={m.id} match={m} onRespond={handleRespond} />
        ))}
      </div>

      {showProposer && (
        <ProposeMatchModal
          onClose={() => setShowProposer(false)}
          onCreated={async () => {
            setShowProposer(false)
            await refresh()
          }}
        />
      )}
    </div>
  )
}

function MatchCard({ match, onRespond }) {
  const statusColor = STATUS_COLORS[match.status] || '#00d4ff'
  const eatery = match.eateries || {}
  const when = new Date(match.scheduled_at)

  return (
    <div
      style={{
        padding: 18,
        borderRadius: 12,
        background: 'rgba(0, 20, 40, 0.65)',
        border: `1px solid ${statusColor}55`,
        boxShadow: `0 0 24px ${statusColor}14 inset`,
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: 12,
        }}
      >
        <div style={{ flex: 1 }}>
          <div
            style={{
              fontFamily: 'monospace',
              fontSize: 10,
              letterSpacing: 2,
              color: statusColor,
              textTransform: 'uppercase',
              marginBottom: 3,
            }}
          >
            {match.status}
            {match.compatibility_score > 0 && ` · ${match.compatibility_score}% match`}
          </div>
          <div style={{ fontSize: 16, fontWeight: 600, color: '#e6f6ff' }}>
            {eatery.name || '(unknown eatery)'}
          </div>
          <div
            style={{
              marginTop: 4,
              fontSize: 12,
              color: 'rgba(230, 246, 255, 0.55)',
              fontFamily: 'monospace',
            }}
          >
            {when.toLocaleString(undefined, {
              weekday: 'short',
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
            {' · '}
            {match.meal_type.toUpperCase()}
          </div>
          {match.match_factors && Object.keys(match.match_factors).length > 0 && (
            <div
              style={{
                marginTop: 10,
                display: 'flex',
                gap: 10,
                flexWrap: 'wrap',
                fontFamily: 'monospace',
                fontSize: 10,
                color: 'rgba(230, 246, 255, 0.5)',
              }}
            >
              {Object.entries(match.match_factors).map(([k, v]) => (
                <span
                  key={k}
                  style={{
                    padding: '2px 8px',
                    border: '1px solid rgba(0, 212, 255, 0.25)',
                    borderRadius: 4,
                  }}
                >
                  {k.replace('_', ' ')}: {v}
                </span>
              ))}
            </div>
          )}
        </div>
        {match.status === 'proposed' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <button
              type="button"
              onClick={() => onRespond(match.id, 'accepted')}
              style={{
                padding: '8px 14px',
                border: '1px solid #7fffa0',
                background: 'rgba(127, 255, 160, 0.12)',
                color: '#7fffa0',
                fontFamily: 'monospace',
                fontSize: 10,
                letterSpacing: 2,
                cursor: 'pointer',
                borderRadius: 6,
              }}
            >
              ACCEPT
            </button>
            <button
              type="button"
              onClick={() => onRespond(match.id, 'declined')}
              style={{
                padding: '8px 14px',
                border: '1px solid rgba(255, 80, 80, 0.4)',
                background: 'rgba(255, 80, 80, 0.08)',
                color: 'rgba(255, 120, 120, 0.85)',
                fontFamily: 'monospace',
                fontSize: 10,
                letterSpacing: 2,
                cursor: 'pointer',
                borderRadius: 6,
              }}
            >
              DECLINE
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function ProposeMatchModal({ onClose, onCreated }) {
  const [users, setUsers] = useState([])
  const [eateries, setEateries] = useState([])
  const [userId, setUserId] = useState('')
  const [eateryId, setEateryId] = useState('')
  const [when, setWhen] = useState('')
  const [mealType, setMealType] = useState('lunch')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    ;(async () => {
      try {
        const [u, e] = await Promise.all([api.listOtherUsers(), api.listEateries({ limit: 100 })])
        setUsers(u.users || [])
        setEateries(e.eateries || [])
      } catch (err) {
        setError(err?.message || 'Failed to load pickers')
      }
    })()
  }, [])

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    if (!userId || !eateryId || !when) {
      setError('All fields are required.')
      return
    }
    setBusy(true)
    try {
      await api.proposeMatch({
        other_user_id: userId,
        eatery_id: eateryId,
        scheduled_at: new Date(when).toISOString(),
        meal_type: mealType,
      })
      onCreated()
    } catch (e2) {
      setError(e2?.message || 'Propose failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={modalBackdrop} onClick={onClose}>
      <form style={modalCard} onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <div
          style={{
            fontFamily: 'monospace',
            fontSize: 11,
            letterSpacing: 3,
            color: '#ff6b9d',
          }}
        >
          PROPOSE MATCH //
        </div>
        <h2 style={{ margin: '4px 0 16px', fontSize: 20 }}>Start a new meal match</h2>

        <label style={labelStack}>
          <span style={labelText}>WITH USER</span>
          <select
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            style={input}
          >
            <option value="">— pick a user —</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name || u.id.slice(0, 8)}
              </option>
            ))}
          </select>
        </label>

        <label style={labelStack}>
          <span style={labelText}>EATERY</span>
          <select
            value={eateryId}
            onChange={(e) => setEateryId(e.target.value)}
            style={input}
          >
            <option value="">— pick a restaurant —</option>
            {eateries.map((e) => (
              <option key={e.id} value={e.id}>
                {e.name} ({e.cuisine})
              </option>
            ))}
          </select>
        </label>

        <div style={{ display: 'flex', gap: 10 }}>
          <label style={{ ...labelStack, flex: 1 }}>
            <span style={labelText}>DATE & TIME</span>
            <input
              type="datetime-local"
              value={when}
              onChange={(e) => setWhen(e.target.value)}
              style={input}
            />
          </label>
          <label style={{ ...labelStack, flex: 0, minWidth: 120 }}>
            <span style={labelText}>MEAL</span>
            <select
              value={mealType}
              onChange={(e) => setMealType(e.target.value)}
              style={input}
            >
              <option value="breakfast">Breakfast</option>
              <option value="lunch">Lunch</option>
              <option value="dinner">Dinner</option>
            </select>
          </label>
        </div>

        {error && <div style={{ ...errorBox, marginTop: 10 }}>{error}</div>}

        <div style={{ display: 'flex', gap: 10, marginTop: 18 }}>
          <button type="button" onClick={onClose} style={secondaryBtn}>
            CANCEL
          </button>
          <button type="submit" disabled={busy} style={primaryBtn}>
            {busy ? 'PROPOSING…' : 'PROPOSE'}
          </button>
        </div>
      </form>
    </div>
  )
}

const primaryBtn = {
  padding: '10px 18px',
  borderRadius: 8,
  border: '1px solid #ff6b9d',
  background: 'rgba(255, 107, 157, 0.18)',
  color: '#ff6b9d',
  fontFamily: 'monospace',
  fontSize: 12,
  letterSpacing: 2,
  cursor: 'pointer',
  fontWeight: 600,
}
const secondaryBtn = {
  padding: '10px 18px',
  borderRadius: 8,
  border: '1px solid rgba(230, 246, 255, 0.2)',
  background: 'transparent',
  color: 'rgba(230, 246, 255, 0.75)',
  fontFamily: 'monospace',
  fontSize: 12,
  letterSpacing: 2,
  cursor: 'pointer',
}
const input = {
  padding: '10px 12px',
  borderRadius: 8,
  border: '1px solid rgba(0, 212, 255, 0.3)',
  background: 'rgba(0, 20, 40, 0.5)',
  color: '#e6f6ff',
  fontSize: 13,
  outline: 'none',
}
const labelStack = { display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 12 }
const labelText = {
  fontSize: 10,
  letterSpacing: 2,
  fontFamily: 'monospace',
  color: 'rgba(0, 212, 255, 0.55)',
}
const errorBox = {
  padding: '8px 10px',
  borderRadius: 6,
  background: 'rgba(255, 80, 80, 0.1)',
  border: '1px solid rgba(255, 80, 80, 0.35)',
  color: 'rgba(255, 170, 170, 0.95)',
  fontSize: 11,
  fontFamily: 'monospace',
}
const emptyBox = {
  padding: 20,
  borderRadius: 12,
  border: '1px dashed rgba(0, 212, 255, 0.25)',
  background: 'rgba(0, 20, 40, 0.4)',
  color: 'rgba(230, 246, 255, 0.55)',
  fontSize: 13,
  textAlign: 'center',
  lineHeight: 1.6,
}
const modalBackdrop = {
  position: 'fixed',
  inset: 0,
  background: 'rgba(0, 5, 15, 0.75)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 200,
  backdropFilter: 'blur(4px)',
}
const modalCard = {
  width: 440,
  maxWidth: '92vw',
  padding: 26,
  borderRadius: 14,
  background: '#020d1a',
  border: '1px solid rgba(255, 107, 157, 0.4)',
  boxShadow: '0 0 40px rgba(255, 107, 157, 0.2)',
  color: '#e6f6ff',
  fontFamily:
    'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
}
