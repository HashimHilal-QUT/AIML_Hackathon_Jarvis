import { useState } from 'react'

/**
 * Renders when /api/meal-buddy/* returns 412 schema_not_ready. Offers a
 * copy-to-clipboard button and a direct link to the Supabase SQL editor.
 */
export default function MealBuddySetupBanner({ info, onRetry }) {
  const [sql, setSql] = useState(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  const loadSql = async () => {
    if (sql) return sql
    setLoading(true)
    try {
      const res = await fetch('/api/meal-buddy/setup-sql')
      if (!res.ok) throw new Error('Failed to load setup SQL')
      const text = await res.text()
      setSql(text)
      return text
    } catch (e) {
      alert(e?.message || 'Could not load SQL')
      return null
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = async () => {
    const text = await loadSql()
    if (!text) return
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    } catch {
      alert('Copy failed — expand the SQL panel and copy manually.')
    }
  }

  return (
    <div
      style={{
        padding: '22px 24px',
        borderRadius: 14,
        background:
          'linear-gradient(180deg, rgba(60, 20, 40, 0.65), rgba(30, 10, 20, 0.85))',
        border: '1px solid #ff6b9d88',
        boxShadow: '0 0 32px rgba(255, 107, 157, 0.15) inset',
        marginBottom: 24,
        color: '#e6f6ff',
      }}
    >
      <div
        style={{
          fontFamily: 'monospace',
          fontSize: 11,
          letterSpacing: 3,
          color: '#ff6b9d',
          marginBottom: 4,
        }}
      >
        ⚠ SETUP REQUIRED //
      </div>
      <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 6 }}>
        Meal & Friends database migration
      </div>
      <p
        style={{
          color: 'rgba(230, 246, 255, 0.7)',
          fontSize: 13,
          lineHeight: 1.6,
          margin: '6px 0 14px',
          maxWidth: 720,
        }}
      >
        The Meal & Friends feature needs six new tables (<code>dining_preferences</code>,{' '}
        <code>eateries</code>, <code>dining_picks</code>,{' '}
        <code>dining_availability</code>, <code>meal_matches</code>,{' '}
        <code>dining_stats</code>) in your Supabase database. Same deal as the Subjects
        migration — paste the SQL into the Supabase dashboard once. Takes about 15 seconds.
      </p>

      <ol
        style={{
          color: 'rgba(230, 246, 255, 0.8)',
          fontSize: 13,
          lineHeight: 1.8,
          paddingLeft: 20,
          marginBottom: 14,
        }}
      >
        <li>Click <strong>Copy SQL</strong>.</li>
        <li>
          Open the{' '}
          <a
            href={
              info?.dashboard_url ||
              'https://supabase.com/dashboard/project/eredinmxmdlgeqfmgtsm/sql/new'
            }
            target="_blank"
            rel="noreferrer"
            style={{ color: '#00d4ff', fontWeight: 600 }}
          >
            Supabase SQL Editor ↗
          </a>
          .
        </li>
        <li>Paste (⌘+V), click <strong>Run</strong>.</li>
        <li>Come back and click <strong>Retry</strong>.</li>
      </ol>

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <button
          type="button"
          onClick={handleCopy}
          disabled={loading}
          style={{
            padding: '10px 16px',
            borderRadius: 8,
            border: '1px solid #ff6b9d',
            background: 'rgba(255, 107, 157, 0.2)',
            color: '#ff6b9d',
            fontFamily: 'monospace',
            fontSize: 12,
            letterSpacing: 2,
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          {loading ? 'LOADING…' : copied ? '✓ COPIED' : '📋 COPY SQL'}
        </button>
        <a
          href={
            info?.dashboard_url ||
            'https://supabase.com/dashboard/project/eredinmxmdlgeqfmgtsm/sql/new'
          }
          target="_blank"
          rel="noreferrer"
          style={{
            padding: '10px 16px',
            borderRadius: 8,
            border: '1px solid #00d4ff',
            background: 'rgba(0, 212, 255, 0.15)',
            color: '#00d4ff',
            fontFamily: 'monospace',
            fontSize: 12,
            letterSpacing: 2,
            fontWeight: 600,
            textDecoration: 'none',
          }}
        >
          OPEN SQL EDITOR ↗
        </a>
        <button
          type="button"
          onClick={onRetry}
          style={{
            padding: '10px 16px',
            borderRadius: 8,
            border: '1px solid rgba(230, 246, 255, 0.3)',
            background: 'transparent',
            color: 'rgba(230, 246, 255, 0.85)',
            fontFamily: 'monospace',
            fontSize: 12,
            letterSpacing: 2,
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          ↻ RETRY
        </button>
      </div>

      {sql && (
        <details style={{ marginTop: 16 }}>
          <summary
            style={{
              color: 'rgba(230, 246, 255, 0.55)',
              fontSize: 12,
              fontFamily: 'monospace',
              cursor: 'pointer',
            }}
          >
            Show SQL ({sql.length} chars)
          </summary>
          <pre
            style={{
              marginTop: 10,
              padding: 14,
              background: 'rgba(0, 10, 20, 0.85)',
              border: '1px solid rgba(0, 212, 255, 0.15)',
              borderRadius: 8,
              color: 'rgba(230, 246, 255, 0.85)',
              fontFamily: 'ui-monospace, monospace',
              fontSize: 11,
              lineHeight: 1.5,
              maxHeight: 320,
              overflow: 'auto',
              whiteSpace: 'pre-wrap',
            }}
          >
            {sql}
          </pre>
        </details>
      )}
    </div>
  )
}
