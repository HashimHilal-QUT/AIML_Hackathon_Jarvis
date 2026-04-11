import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import MealBuddyNav from '../components/MealBuddyNav'
import MealBuddySetupBanner from '../components/MealBuddySetupBanner'

export default function MealBuddyHub() {
  const [stats, setStats] = useState(null)
  const [prefs, setPrefs] = useState(null)
  const [loading, setLoading] = useState(true)
  const [setupInfo, setSetupInfo] = useState(null)
  const [error, setError] = useState(null)

  const refresh = async () => {
    setLoading(true)
    setError(null)
    setSetupInfo(null)
    try {
      const [s, p] = await Promise.all([api.getDiningStats(), api.getDiningPrefs()])
      setStats(s)
      setPrefs(p)
    } catch (e) {
      if (e?.status === 412 && e?.structured?.error === 'schema_not_ready') {
        setSetupInfo(e.structured)
      } else {
        setError(e?.message || 'Failed to load')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto' }}>
      <MealBuddyNav />
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 34, margin: 0, fontWeight: 700 }}>
          Find a dining buddy
        </h1>
        <p
          style={{
            color: 'rgba(230, 246, 255, 0.6)',
            fontSize: 14,
            marginTop: 8,
            maxWidth: 620,
          }}
        >
          Set your cuisines, budget, and dietary flags, pick restaurants you want
          to try, mark when you're free, and Jarvis will match you with another
          student for lunch or dinner.
        </p>
      </header>

      {setupInfo && <MealBuddySetupBanner info={setupInfo} onRetry={refresh} />}
      {error && <div style={errorBox}>{error}</div>}

      {!setupInfo && (
        <>
          <div style={dataStrip}>
            <DataItem label="Matches Made" value={stats?.matches_made ?? '—'} color="#00d4ff" />
            <DataItem label="Points" value={stats?.points_earned ?? '—'} color="#f5a623" />
            <DataItem label="Eateries Visited" value={stats?.eateries_visited ?? '—'} color="#7fffa0" />
            <DataItem label="Cuisines Set" value={(prefs?.cuisines || []).length} color="#ff6b9d" />
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
              gap: 16,
              marginTop: 20,
            }}
          >
            <Card
              to="/meal-buddy/preferences"
              accent="#ff6b9d"
              emoji="🍜"
              title="PREFERENCES"
              subtitle="Cuisines · Budget · Dietary"
              body="Configure your culinary preference matrix that drives every match."
            />
            <Card
              to="/meal-buddy/discover"
              accent="#00d4ff"
              emoji="🔥"
              title="DISCOVER"
              subtitle="Hot list + curated picks"
              body="Browse trending eateries and pick up to 3 to initiate dining matches."
            />
            <Card
              to="/meal-buddy/availability"
              accent="#f5a623"
              emoji="📆"
              title="AVAILABILITY"
              subtitle="Weekly schedule"
              body="Mark the lunch and dinner slots you're free for the upcoming week."
            />
            <Card
              to="/meal-buddy/matches"
              accent="#7fffa0"
              emoji="🤝"
              title="MATCHES"
              subtitle="Proposed & confirmed"
              body="Review pending match proposals, see compatibility scores, accept or decline."
            />
          </div>
        </>
      )}
      {loading && !setupInfo && (
        <div style={{ marginTop: 20, color: 'rgba(230, 246, 255, 0.5)', fontFamily: 'monospace' }}>
          Loading…
        </div>
      )}
    </div>
  )
}

function DataItem({ label, value, color }) {
  return (
    <div
      style={{
        flex: 1,
        padding: '10px 16px',
        borderRight: '1px solid rgba(0, 212, 255, 0.18)',
        fontFamily: 'monospace',
        fontSize: 10,
      }}
    >
      <div
        style={{
          color: 'rgba(230, 246, 255, 0.45)',
          letterSpacing: 2,
          textTransform: 'uppercase',
          marginBottom: 3,
        }}
      >
        {label}
      </div>
      <div style={{ color, fontSize: 16, fontWeight: 600 }}>{value}</div>
    </div>
  )
}

function Card({ to, accent, emoji, title, subtitle, body }) {
  return (
    <Link
      to={to}
      style={{
        display: 'block',
        textDecoration: 'none',
        color: 'inherit',
        padding: 22,
        borderRadius: 12,
        background:
          'linear-gradient(180deg, rgba(0, 30, 60, 0.7), rgba(0, 15, 30, 0.9))',
        border: `1px solid ${accent}55`,
        boxShadow: `0 0 24px ${accent}1f inset`,
        transition: 'transform 120ms ease-out, box-shadow 120ms ease-out',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)'
        e.currentTarget.style.boxShadow = `0 0 32px ${accent}33 inset, 0 10px 28px ${accent}22`
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = `0 0 24px ${accent}1f inset`
      }}
    >
      <div style={{ fontSize: 28, marginBottom: 10 }}>{emoji}</div>
      <div
        style={{
          fontFamily: 'monospace',
          fontSize: 10,
          letterSpacing: 3,
          color: accent,
        }}
      >
        {title}
      </div>
      <div style={{ fontSize: 18, fontWeight: 600, marginTop: 4 }}>{subtitle}</div>
      <div
        style={{
          fontSize: 12,
          color: 'rgba(230, 246, 255, 0.55)',
          marginTop: 8,
          lineHeight: 1.5,
        }}
      >
        {body}
      </div>
    </Link>
  )
}

const dataStrip = {
  display: 'flex',
  border: '1px solid rgba(0, 212, 255, 0.25)',
  borderRadius: 8,
  overflow: 'hidden',
  marginTop: 8,
}

const errorBox = {
  padding: '10px 14px',
  marginBottom: 14,
  borderRadius: 8,
  background: 'rgba(255, 80, 80, 0.1)',
  border: '1px solid rgba(255, 80, 80, 0.4)',
  color: 'rgba(255, 170, 170, 0.95)',
  fontSize: 13,
  fontFamily: 'monospace',
}
