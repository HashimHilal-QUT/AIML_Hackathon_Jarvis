import { useCallback, useEffect, useState } from 'react'
import { api } from '../lib/api'
import MealBuddyNav from '../components/MealBuddyNav'
import MealBuddySetupBanner from '../components/MealBuddySetupBanner'

export default function DiscoverPage() {
  const [eateries, setEateries] = useState([])
  const [trending, setTrending] = useState([])
  const [picks, setPicks] = useState([])
  const [loading, setLoading] = useState(true)
  const [setupInfo, setSetupInfo] = useState(null)
  const [error, setError] = useState(null)

  const pickedIds = new Set(picks.map((p) => p.eatery_id))

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    setSetupInfo(null)
    try {
      const [all, hot, myPicks] = await Promise.all([
        api.listEateries({ limit: 100 }),
        api.listEateries({ trending_only: true }),
        api.getPicks(),
      ])
      setEateries(all.eateries || [])
      setTrending(hot.eateries || [])
      setPicks(myPicks.picks || [])
    } catch (e) {
      if (e?.status === 412 && e?.structured?.error === 'schema_not_ready') {
        setSetupInfo(e.structured)
      } else {
        setError(e?.message || 'Failed to load eateries')
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const togglePick = async (eateryId) => {
    try {
      if (pickedIds.has(eateryId)) {
        await api.removePick(eateryId)
      } else {
        if (picks.length >= 3) {
          alert('You already have 3 picks. Remove one first.')
          return
        }
        await api.addPick(eateryId)
      }
      const myPicks = await api.getPicks()
      setPicks(myPicks.picks || [])
    } catch (e) {
      alert(e?.message || 'Pick update failed')
    }
  }

  if (setupInfo) {
    return (
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <MealBuddyNav />
        <MealBuddySetupBanner info={setupInfo} onRetry={refresh} />
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <MealBuddyNav />
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 32, margin: 0, fontWeight: 700 }}>
          Hot list & curated picks
        </h1>
        <div
          style={{
            marginTop: 6,
            fontFamily: 'monospace',
            fontSize: 12,
            color: 'rgba(230, 246, 255, 0.55)',
          }}
        >
          SELECTED: <span style={{ color: '#f5a623' }}>{picks.length}/3</span>
        </div>
      </header>

      {error && <div style={errorBox}>{error}</div>}

      {/* HOT LIST */}
      <section style={{ marginBottom: 28 }}>
        <div
          style={{
            fontFamily: 'monospace',
            fontSize: 10,
            letterSpacing: 2,
            color: '#f5a623',
            marginBottom: 10,
          }}
        >
          // TRENDING NOW — THE HOT LIST
        </div>
        <div
          style={{
            display: 'flex',
            gap: 16,
            overflowX: 'auto',
            paddingBottom: 8,
          }}
        >
          {trending.map((e, i) => (
            <HotCard
              key={e.id}
              eatery={e}
              rank={i + 1}
              picked={pickedIds.has(e.id)}
              onToggle={() => togglePick(e.id)}
            />
          ))}
          {!loading && !trending.length && (
            <div
              style={{
                color: 'rgba(230, 246, 255, 0.5)',
                fontSize: 12,
                fontFamily: 'monospace',
              }}
            >
              No trending eateries yet.
            </div>
          )}
        </div>
      </section>

      {/* ALL EATERIES GRID */}
      <section>
        <div
          style={{
            fontFamily: 'monospace',
            fontSize: 10,
            letterSpacing: 2,
            color: '#00d4ff',
            marginBottom: 10,
          }}
        >
          // CURATED MATCH CANDIDATES ({eateries.length})
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
            gap: 12,
          }}
        >
          {eateries.map((e) => (
            <RestCard
              key={e.id}
              eatery={e}
              picked={pickedIds.has(e.id)}
              onToggle={() => togglePick(e.id)}
            />
          ))}
        </div>
      </section>
    </div>
  )
}

function HotCard({ eatery, rank, picked, onToggle }) {
  const rankColors = ['#f5a623', '#00d4ff', '#7fffa0']
  return (
    <div
      style={{
        flex: '0 0 260px',
        position: 'relative',
        borderRadius: 10,
        border: '1px solid rgba(0, 212, 255, 0.3)',
        overflow: 'hidden',
        background: 'rgba(0, 20, 40, 0.6)',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: -2,
          left: -2,
          zIndex: 10,
          padding: '6px 14px',
          fontFamily: 'monospace',
          fontWeight: 700,
          fontSize: 13,
          letterSpacing: 1,
          background: rankColors[rank - 1] || '#00d4ff',
          color: '#020d1a',
          transform: 'rotate(-8deg)',
          boxShadow: '0 0 12px rgba(0, 0, 0, 0.5)',
        }}
      >
        NO.{rank}
      </div>
      <img
        src={eatery.image_url}
        alt=""
        style={{
          width: '100%',
          height: 200,
          objectFit: 'cover',
          filter: 'brightness(0.7) saturate(0.85)',
          display: 'block',
        }}
      />
      <button
        type="button"
        onClick={onToggle}
        style={{
          position: 'absolute',
          top: 10,
          right: 10,
          zIndex: 20,
          padding: '6px 10px',
          borderRadius: 4,
          border: picked ? '1px solid #f5a623' : '1px solid rgba(0, 212, 255, 0.4)',
          background: picked ? 'rgba(245, 166, 35, 0.25)' : 'rgba(2, 13, 26, 0.75)',
          color: picked ? '#f5a623' : '#00d4ff',
          fontFamily: 'monospace',
          fontSize: 11,
          cursor: 'pointer',
          backdropFilter: 'blur(6px)',
        }}
      >
        {picked ? '✓' : '+'}
      </button>
      <div
        style={{
          padding: 14,
          background:
            'linear-gradient(to top, rgba(2, 13, 26, 0.95), transparent)',
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
        }}
      >
        <div
          style={{
            fontFamily: 'monospace',
            fontSize: 14,
            color: '#00d4ff',
            letterSpacing: 1,
            marginBottom: 3,
          }}
        >
          {eatery.name}
        </div>
        <div style={{ fontSize: 11, color: 'rgba(230, 246, 255, 0.55)', fontFamily: 'monospace' }}>
          {eatery.blurb}
        </div>
        <div style={{ marginTop: 6, display: 'flex', gap: 6 }}>
          {eatery.rating && (
            <span
              style={{
                padding: '2px 8px',
                border: '1px solid #f5a623',
                color: '#f5a623',
                fontFamily: 'monospace',
                fontSize: 9,
                letterSpacing: 1,
              }}
            >
              {eatery.rating} ★
            </span>
          )}
          {(eatery.tags || []).slice(0, 1).map((t) => (
            <span
              key={t}
              style={{
                padding: '2px 8px',
                border: '1px solid rgba(230, 246, 255, 0.25)',
                color: 'rgba(230, 246, 255, 0.5)',
                fontFamily: 'monospace',
                fontSize: 9,
                letterSpacing: 1,
                textTransform: 'uppercase',
              }}
            >
              {t.replace('_', ' ')}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

function RestCard({ eatery, picked, onToggle }) {
  return (
    <div
      onClick={onToggle}
      style={{
        borderRadius: 10,
        border: picked
          ? '1px solid #f5a623'
          : '1px solid rgba(0, 212, 255, 0.2)',
        background: 'rgba(0, 20, 40, 0.7)',
        cursor: 'pointer',
        overflow: 'hidden',
        boxShadow: picked ? '0 0 16px rgba(245, 166, 35, 0.2)' : 'none',
        transition: 'all 120ms ease-out',
      }}
    >
      <div style={{ position: 'relative', height: 140, overflow: 'hidden' }}>
        <img
          src={eatery.image_url}
          alt=""
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'brightness(0.7) saturate(0.8)',
          }}
        />
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation()
            onToggle()
          }}
          style={{
            position: 'absolute',
            top: 8,
            right: 8,
            padding: '4px 8px',
            borderRadius: 4,
            border: picked ? '1px solid #f5a623' : '1px solid rgba(0, 212, 255, 0.4)',
            background: picked ? 'rgba(245, 166, 35, 0.25)' : 'rgba(2, 13, 26, 0.75)',
            color: picked ? '#f5a623' : '#00d4ff',
            fontFamily: 'monospace',
            fontSize: 10,
            cursor: 'pointer',
          }}
        >
          {picked ? '✓' : '+'}
        </button>
      </div>
      <div style={{ padding: 12 }}>
        <div
          style={{
            fontFamily: 'monospace',
            fontSize: 12,
            color: '#00d4ff',
            letterSpacing: 1,
            marginBottom: 3,
          }}
        >
          {eatery.name}
        </div>
        <div
          style={{
            fontSize: 11,
            color: 'rgba(230, 246, 255, 0.5)',
            fontFamily: 'monospace',
            marginBottom: 8,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {eatery.blurb}
        </div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontFamily: 'monospace',
            fontSize: 10,
          }}
        >
          <span style={{ color: '#f5a623' }}>
            ${eatery.price_low}–${eatery.price_high}
          </span>
          <span style={{ color: 'rgba(230, 246, 255, 0.4)' }}>
            {eatery.cuisine}
          </span>
        </div>
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
