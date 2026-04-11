import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

const COLOR_CHOICES = [
  '#00d4ff',
  '#f5a623',
  '#7fffa0',
  '#ff6b9d',
  '#b794f6',
  '#48dbfb',
  '#ffb84c',
]

export default function SubjectsListPage() {
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [setupInfo, setSetupInfo] = useState(null)
  const [showCreate, setShowCreate] = useState(false)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    setSetupInfo(null)
    try {
      const res = await api.listSubjects()
      setSubjects(res?.subjects || [])
    } catch (e) {
      // Structured "schema not ready" signal from the backend: render the
      // setup banner instead of a generic error.
      if (e?.status === 412 && e?.structured?.error === 'schema_not_ready') {
        setSetupInfo(e.structured)
      } else {
        setError(e?.message || 'Failed to load subjects')
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          marginBottom: 24,
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
            COURSE CONSOLE //
          </div>
          <h1 style={{ fontSize: 34, margin: 0, fontWeight: 700 }}>
            Your subjects
          </h1>
          <p
            style={{
              color: 'rgba(230, 246, 255, 0.6)',
              fontSize: 14,
              marginTop: 8,
              maxWidth: 680,
            }}
          >
            Add your courses with their syllabus, modules, assignment rubrics,
            and slides. Jarvis uses this as context when you ask for help.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowCreate(true)}
          style={primaryBtn}
        >
          + NEW SUBJECT
        </button>
      </header>

      {setupInfo && <SetupBanner info={setupInfo} onRetry={refresh} />}
      {error && <div style={errorBox}>{error}</div>}
      {loading && !subjects.length && !setupInfo && (
        <div style={infoText}>Loading…</div>
      )}

      {!setupInfo && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
            gap: 16,
          }}
        >
          {subjects.map((s) => (
            <SubjectCard key={s.id} subject={s} />
          ))}
          {!loading && !subjects.length && (
            <div style={emptyBox}>
              No subjects yet. Click <strong>+ NEW SUBJECT</strong> to add one.
            </div>
          )}
        </div>
      )}

      {showCreate && (
        <CreateSubjectModal
          onClose={() => setShowCreate(false)}
          onCreated={async () => {
            setShowCreate(false)
            await refresh()
          }}
        />
      )}
    </div>
  )
}

function SubjectCard({ subject }) {
  const color = subject.color || '#00d4ff'
  return (
    <Link
      to={`/subjects/${subject.id}`}
      style={{
        display: 'block',
        textDecoration: 'none',
        color: 'inherit',
        padding: 18,
        borderRadius: 12,
        background:
          'linear-gradient(180deg, rgba(0, 30, 60, 0.7), rgba(0, 15, 30, 0.9))',
        border: `1px solid ${color}55`,
        boxShadow: `0 0 24px ${color}1f inset`,
        transition: 'transform 120ms ease-out, box-shadow 120ms ease-out',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)'
        e.currentTarget.style.boxShadow = `0 0 28px ${color}33 inset, 0 8px 24px ${color}22`
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = `0 0 24px ${color}1f inset`
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          fontFamily: 'monospace',
          fontSize: 10,
          letterSpacing: 2,
          color,
        }}
      >
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: color,
            boxShadow: `0 0 8px ${color}`,
          }}
        />
        {subject.code || 'NO-CODE'}
        {subject.term ? ` · ${subject.term}` : ''}
      </div>
      <div style={{ fontSize: 18, fontWeight: 600, marginTop: 6 }}>
        {subject.name}
      </div>
      {subject.description && (
        <div
          style={{
            fontSize: 12,
            color: 'rgba(230, 246, 255, 0.55)',
            marginTop: 8,
            lineHeight: 1.5,
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          {subject.description}
        </div>
      )}
    </Link>
  )
}

function SetupBanner({ info, onRetry }) {
  const [sql, setSql] = useState(null)
  const [loadingSql, setLoadingSql] = useState(false)
  const [copied, setCopied] = useState(false)

  const loadSql = async () => {
    if (sql) return sql
    setLoadingSql(true)
    try {
      const res = await fetch('/api/subjects/setup-sql')
      if (!res.ok) throw new Error('Failed to load setup SQL')
      const text = await res.text()
      setSql(text)
      return text
    } catch (e) {
      alert(e?.message || 'Could not load SQL')
      return null
    } finally {
      setLoadingSql(false)
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
      alert('Copy failed — please select the SQL below and copy manually.')
    }
  }

  return (
    <div
      style={{
        padding: '22px 24px',
        borderRadius: 14,
        background:
          'linear-gradient(180deg, rgba(60, 30, 0, 0.6), rgba(30, 15, 0, 0.8))',
        border: '1px solid #f5a62388',
        boxShadow: '0 0 32px rgba(245, 166, 35, 0.18) inset',
        marginBottom: 24,
        color: '#e6f6ff',
      }}
    >
      <div
        style={{
          fontFamily: 'monospace',
          fontSize: 11,
          letterSpacing: 3,
          color: '#f5a623',
          marginBottom: 4,
        }}
      >
        ⚠ SETUP REQUIRED //
      </div>
      <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 6 }}>
        One-time database migration
      </div>
      <p
        style={{
          color: 'rgba(230, 246, 255, 0.7)',
          fontSize: 13,
          lineHeight: 1.6,
          margin: '6px 0 14px',
          maxWidth: 680,
        }}
      >
        The Subjects feature needs two new tables (<code>subjects</code> and{' '}
        <code>subject_materials</code>) in your Supabase database. Postgres
        DDL can't go through the service-role REST API, so you need to paste
        the SQL into your Supabase dashboard once. Takes about 15 seconds.
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
        <li>
          Click <strong>Copy SQL</strong> below.
        </li>
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
        <li>
          Come back and click <strong>Retry</strong> — the page will reload
          with the new tables.
        </li>
      </ol>

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <button
          type="button"
          onClick={handleCopy}
          disabled={loadingSql}
          style={{
            padding: '10px 16px',
            borderRadius: 8,
            border: '1px solid #f5a623',
            background: 'rgba(245, 166, 35, 0.2)',
            color: '#f5a623',
            fontFamily: 'monospace',
            fontSize: 12,
            letterSpacing: 2,
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          {loadingSql ? 'LOADING…' : copied ? '✓ COPIED' : '📋 COPY SQL'}
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

function CreateSubjectModal({ onClose, onCreated }) {
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [term, setTerm] = useState('')
  const [color, setColor] = useState(COLOR_CHOICES[0])
  const [description, setDescription] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    if (!name.trim()) {
      setError('Name is required.')
      return
    }
    setSaving(true)
    try {
      await api.createSubject({
        name: name.trim(),
        code: code.trim() || undefined,
        term: term.trim() || undefined,
        color,
        description: description.trim() || undefined,
      })
      onCreated()
    } catch (err) {
      setError(err?.message || 'Failed to create subject')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={modalBackdrop} onClick={onClose}>
      <form
        style={modalCard}
        onClick={(e) => e.stopPropagation()}
        onSubmit={submit}
      >
        <div
          style={{
            fontFamily: 'monospace',
            fontSize: 11,
            letterSpacing: 3,
            color: 'rgba(0, 212, 255, 0.6)',
          }}
        >
          NEW SUBJECT //
        </div>
        <h2 style={{ margin: '2px 0 16px', fontSize: 20 }}>Add a course</h2>

        <label style={labelStack}>
          <span style={labelText}>NAME</span>
          <input
            autoFocus
            value={name}
            onChange={(e) => setName(e.target.value)}
            style={input}
            placeholder="Machine Learning"
          />
        </label>
        <div style={{ display: 'flex', gap: 10 }}>
          <label style={{ ...labelStack, flex: 1 }}>
            <span style={labelText}>CODE</span>
            <input
              value={code}
              onChange={(e) => setCode(e.target.value)}
              style={input}
              placeholder="IFN680"
            />
          </label>
          <label style={{ ...labelStack, flex: 1 }}>
            <span style={labelText}>TERM</span>
            <input
              value={term}
              onChange={(e) => setTerm(e.target.value)}
              style={input}
              placeholder="Semester 1 2026"
            />
          </label>
        </div>
        <label style={labelStack}>
          <span style={labelText}>DESCRIPTION</span>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            style={{ ...input, minHeight: 70, fontFamily: 'inherit' }}
            placeholder="Optional short description"
          />
        </label>
        <label style={labelStack}>
          <span style={labelText}>COLOR</span>
          <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
            {COLOR_CHOICES.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setColor(c)}
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: '50%',
                  border:
                    color === c
                      ? '2px solid #fff'
                      : '2px solid transparent',
                  background: c,
                  cursor: 'pointer',
                  boxShadow: `0 0 10px ${c}`,
                }}
              />
            ))}
          </div>
        </label>

        {error && <div style={{ ...errorBox, marginTop: 12 }}>{error}</div>}

        <div style={{ display: 'flex', gap: 10, marginTop: 20 }}>
          <button type="button" onClick={onClose} style={secondaryBtn}>
            CANCEL
          </button>
          <button type="submit" disabled={saving} style={primaryBtn}>
            {saving ? 'CREATING…' : 'CREATE'}
          </button>
        </div>
      </form>
    </div>
  )
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
  padding: '10px 12px',
  borderRadius: 8,
  background: 'rgba(255, 80, 80, 0.1)',
  border: '1px solid rgba(255, 80, 80, 0.4)',
  color: 'rgba(255, 170, 170, 0.95)',
  fontSize: 12,
  fontFamily: 'monospace',
}
const infoText = {
  padding: 20,
  fontSize: 13,
  color: 'rgba(230, 246, 255, 0.55)',
  fontFamily: 'monospace',
}
const emptyBox = {
  gridColumn: '1 / -1',
  padding: 32,
  borderRadius: 12,
  border: '1px dashed rgba(0, 212, 255, 0.25)',
  background: 'rgba(0, 20, 40, 0.4)',
  color: 'rgba(230, 246, 255, 0.55)',
  fontSize: 14,
  textAlign: 'center',
}
const modalBackdrop = {
  position: 'fixed',
  inset: 0,
  background: 'rgba(0, 5, 15, 0.75)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 100,
  backdropFilter: 'blur(4px)',
}
const modalCard = {
  width: 440,
  maxWidth: '92vw',
  padding: 26,
  borderRadius: 14,
  background: '#020d1a',
  border: '1px solid rgba(0, 212, 255, 0.4)',
  boxShadow: '0 0 40px rgba(0, 212, 255, 0.2)',
  color: '#e6f6ff',
  fontFamily: 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
}
