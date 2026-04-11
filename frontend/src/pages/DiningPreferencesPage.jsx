import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import MealBuddyNav from '../components/MealBuddyNav'
import MealBuddySetupBanner from '../components/MealBuddySetupBanner'

const CUISINES = [
  'italian',
  'japanese',
  'mexican',
  'indian',
  'mediterranean',
  'thai',
  'korean',
  'vietnamese',
  'chinese',
  'american',
  'french',
  'greek',
]
const DIETARY = [
  'vegetarian',
  'vegan',
  'gluten_free',
  'halal',
  'kosher',
  'nut_allergy',
  'dairy_free',
  'pescatarian',
]

export default function DiningPreferencesPage() {
  const [prefs, setPrefs] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [setupInfo, setSetupInfo] = useState(null)
  const [error, setError] = useState(null)
  const [toast, setToast] = useState(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    setSetupInfo(null)
    try {
      const p = await api.getDiningPrefs()
      setPrefs({
        cuisines: p.cuisines || [],
        budget_amount: p.budget_amount ?? 35,
        budget_tier: p.budget_tier || '$$',
        dietary_flags: p.dietary_flags || [],
      })
    } catch (e) {
      if (e?.status === 412 && e?.structured?.error === 'schema_not_ready') {
        setSetupInfo(e.structured)
      } else {
        setError(e?.message || 'Failed to load preferences')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const toggleCuisine = (c) => {
    setPrefs((p) => ({
      ...p,
      cuisines: p.cuisines.includes(c) ? p.cuisines.filter((x) => x !== c) : [...p.cuisines, c],
    }))
  }
  const toggleDietary = (d) => {
    setPrefs((p) => ({
      ...p,
      dietary_flags: p.dietary_flags.includes(d)
        ? p.dietary_flags.filter((x) => x !== d)
        : [...p.dietary_flags, d],
    }))
  }
  const setBudgetAmount = (v) => setPrefs((p) => ({ ...p, budget_amount: Number(v) }))
  const setBudgetTier = (t) => setPrefs((p) => ({ ...p, budget_tier: t }))

  const save = async () => {
    setSaving(true)
    setError(null)
    try {
      await api.putDiningPrefs(prefs)
      setToast('Saved ✓')
      setTimeout(() => setToast(null), 2500)
    } catch (e) {
      setError(e?.message || 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  if (setupInfo) {
    return (
      <div style={{ maxWidth: 1000, margin: '0 auto' }}>
        <MealBuddyNav />
        <MealBuddySetupBanner info={setupInfo} onRetry={load} />
      </div>
    )
  }

  if (loading || !prefs) {
    return (
      <div style={{ maxWidth: 1000, margin: '0 auto' }}>
        <MealBuddyNav />
        <div style={{ color: 'rgba(230, 246, 255, 0.6)', fontFamily: 'monospace' }}>
          Loading preferences…
        </div>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <MealBuddyNav />
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 32, margin: 0, fontWeight: 700 }}>
          Tell us what you crave.
        </h1>
        <p
          style={{
            color: 'rgba(230, 246, 255, 0.6)',
            fontSize: 14,
            marginTop: 8,
            maxWidth: 620,
          }}
        >
          Configure your culinary preference matrix. These parameters power the
          matching algorithm and are shared with Jarvis as context.
        </p>
      </header>

      {error && <div style={errorBox}>{error}</div>}

      {/* CUISINE */}
      <Section title="CUISINE MATRIX" icon="🍜" accent="#ff6b9d">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {CUISINES.map((c) => {
            const on = prefs.cuisines.includes(c)
            return (
              <button
                key={c}
                type="button"
                onClick={() => toggleCuisine(c)}
                style={{
                  padding: '8px 16px',
                  borderRadius: 4,
                  border: on ? '1px solid #f5a623' : '1px solid rgba(0, 212, 255, 0.3)',
                  background: on ? 'rgba(245, 166, 35, 0.12)' : 'rgba(0, 212, 255, 0.05)',
                  color: on ? '#f5a623' : 'rgba(230, 246, 255, 0.6)',
                  fontFamily: 'monospace',
                  fontSize: 11,
                  letterSpacing: 1,
                  textTransform: 'uppercase',
                  cursor: 'pointer',
                  boxShadow: on ? '0 0 10px rgba(245, 166, 35, 0.2)' : 'none',
                }}
              >
                {c.replace('_', ' ')}
              </button>
            )
          })}
        </div>
      </Section>

      {/* BUDGET */}
      <Section title="BUDGET THRESHOLD" icon="💰" accent="#f5a623">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div>
            <div
              style={{
                fontFamily: 'monospace',
                fontSize: 10,
                letterSpacing: 1,
                color: 'rgba(230, 246, 255, 0.5)',
                marginBottom: 6,
              }}
            >
              DAILY BUDGET
            </div>
            <div
              style={{
                fontFamily: 'monospace',
                fontSize: 32,
                color: '#00d4ff',
                textShadow: '0 0 12px rgba(0, 212, 255, 0.4)',
                marginBottom: 6,
              }}
            >
              ${prefs.budget_amount}
            </div>
            <input
              type="range"
              min="10"
              max="150"
              value={prefs.budget_amount}
              onChange={(e) => setBudgetAmount(e.target.value)}
              style={{ width: '100%' }}
            />
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontFamily: 'monospace',
                fontSize: 10,
                color: 'rgba(230, 246, 255, 0.4)',
                marginTop: 4,
              }}
            >
              <span>$10</span>
              <span>$150+</span>
            </div>
          </div>
          <div>
            <div
              style={{
                fontFamily: 'monospace',
                fontSize: 10,
                letterSpacing: 1,
                color: 'rgba(230, 246, 255, 0.5)',
                marginBottom: 10,
              }}
            >
              TIER CLASSIFICATION
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6 }}>
              {['$', '$$', '$$$'].map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setBudgetTier(t)}
                  style={{
                    padding: '10px',
                    borderRadius: 4,
                    border:
                      prefs.budget_tier === t
                        ? '1px solid #f5a623'
                        : '1px solid rgba(0, 212, 255, 0.25)',
                    background:
                      prefs.budget_tier === t
                        ? 'rgba(245, 166, 35, 0.15)'
                        : 'rgba(0, 20, 40, 0.4)',
                    color: prefs.budget_tier === t ? '#f5a623' : 'rgba(230, 246, 255, 0.6)',
                    fontFamily: 'monospace',
                    fontSize: 11,
                    cursor: 'pointer',
                    letterSpacing: 1,
                  }}
                >
                  {t} {t === '$' ? 'BUDGET' : t === '$$' ? 'VALUE' : 'PREMIUM'}
                </button>
              ))}
            </div>
          </div>
        </div>
      </Section>

      {/* DIETARY */}
      <Section title="DIETARY PROTOCOLS" icon="🌱" accent="#7fffa0">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {DIETARY.map((d) => {
            const on = prefs.dietary_flags.includes(d)
            return (
              <button
                key={d}
                type="button"
                onClick={() => toggleDietary(d)}
                style={{
                  padding: '8px 16px',
                  borderRadius: 4,
                  border: on ? '1px solid #7fffa0' : '1px solid rgba(0, 212, 255, 0.25)',
                  background: on ? 'rgba(127, 255, 160, 0.12)' : 'rgba(0, 212, 255, 0.04)',
                  color: on ? '#7fffa0' : 'rgba(230, 246, 255, 0.6)',
                  fontFamily: 'monospace',
                  fontSize: 11,
                  letterSpacing: 1,
                  textTransform: 'uppercase',
                  cursor: 'pointer',
                  boxShadow: on ? '0 0 10px rgba(127, 255, 160, 0.2)' : 'none',
                }}
              >
                {d.replace('_', ' ')}
              </button>
            )
          })}
        </div>
      </Section>

      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
          gap: 12,
          alignItems: 'center',
          marginTop: 20,
        }}
      >
        {toast && (
          <span
            style={{
              color: '#7fffa0',
              fontFamily: 'monospace',
              fontSize: 12,
            }}
          >
            {toast}
          </span>
        )}
        <button
          type="button"
          onClick={save}
          disabled={saving}
          style={{
            padding: '12px 24px',
            borderRadius: 8,
            border: '1px solid #ff6b9d',
            background: 'rgba(255, 107, 157, 0.18)',
            color: '#ff6b9d',
            fontFamily: 'monospace',
            fontSize: 12,
            letterSpacing: 2,
            fontWeight: 600,
            cursor: 'pointer',
            opacity: saving ? 0.5 : 1,
          }}
        >
          {saving ? 'SAVING…' : 'SAVE PREFERENCES'}
        </button>
      </div>
    </div>
  )
}

function Section({ title, icon, accent, children }) {
  return (
    <section
      style={{
        marginBottom: 20,
        padding: 20,
        borderRadius: 12,
        background: 'rgba(0, 20, 40, 0.55)',
        border: `1px solid ${accent}33`,
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          marginBottom: 14,
        }}
      >
        <span style={{ fontSize: 22 }}>{icon}</span>
        <div
          style={{
            fontFamily: 'monospace',
            fontSize: 11,
            letterSpacing: 3,
            color: accent,
          }}
        >
          {title} //
        </div>
      </div>
      {children}
    </section>
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
