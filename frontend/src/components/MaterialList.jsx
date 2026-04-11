import { useState } from 'react'

function humanSize(bytes) {
  if (!bytes && bytes !== 0) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export default function MaterialList({ materials, onDelete }) {
  const [expanded, setExpanded] = useState({})

  if (!materials.length) {
    return (
      <div
        style={{
          padding: 20,
          borderRadius: 8,
          background: 'rgba(0, 20, 40, 0.3)',
          border: '1px dashed rgba(0, 212, 255, 0.2)',
          color: 'rgba(230, 246, 255, 0.45)',
          fontSize: 13,
          textAlign: 'center',
          fontStyle: 'italic',
        }}
      >
        Nothing here yet. Add something above — Jarvis will use it as context.
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {materials.map((m) => {
        const isOpen = !!expanded[m.id]
        return (
          <div
            key={m.id}
            style={{
              padding: 14,
              borderRadius: 10,
              background: 'rgba(0, 20, 40, 0.55)',
              border: '1px solid rgba(0, 212, 255, 0.2)',
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
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 14,
                    fontWeight: 600,
                    color: '#e6f6ff',
                    wordBreak: 'break-word',
                  }}
                >
                  {m.title || m.file_name || '(untitled)'}
                </div>
                <div
                  style={{
                    display: 'flex',
                    gap: 10,
                    marginTop: 4,
                    fontSize: 10,
                    fontFamily: 'monospace',
                    color: 'rgba(230, 246, 255, 0.45)',
                    flexWrap: 'wrap',
                  }}
                >
                  <span>{formatDate(m.created_at)}</span>
                  {m.file_type && <span>· {m.file_type}</span>}
                  {typeof m.file_size === 'number' && (
                    <span>· {humanSize(m.file_size)}</span>
                  )}
                  {m.content_text && (
                    <span style={{ color: 'rgba(127, 255, 160, 0.75)' }}>
                      ✓ text extracted
                    </span>
                  )}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                {m.signed_url && (
                  <a
                    href={m.signed_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ ...pillBtn, color: '#f5a623', borderColor: '#f5a62388' }}
                  >
                    OPEN
                  </a>
                )}
                {m.content_text && (
                  <button
                    type="button"
                    onClick={() =>
                      setExpanded((prev) => ({ ...prev, [m.id]: !prev[m.id] }))
                    }
                    style={pillBtn}
                  >
                    {isOpen ? '▲ HIDE' : '▼ SHOW'}
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => {
                    if (confirm(`Delete "${m.title || m.file_name}"?`)) {
                      onDelete(m.id)
                    }
                  }}
                  style={{
                    ...pillBtn,
                    color: 'rgba(255, 120, 120, 0.85)',
                    borderColor: 'rgba(255, 80, 80, 0.4)',
                  }}
                >
                  DEL
                </button>
              </div>
            </div>

            {isOpen && m.content_text && (
              <pre
                style={{
                  marginTop: 12,
                  padding: 12,
                  background: 'rgba(0, 10, 20, 0.7)',
                  border: '1px solid rgba(0, 212, 255, 0.15)',
                  borderRadius: 6,
                  color: 'rgba(230, 246, 255, 0.85)',
                  fontFamily: 'ui-monospace, monospace',
                  fontSize: 11,
                  lineHeight: 1.5,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  maxHeight: 360,
                  overflowY: 'auto',
                }}
              >
                {m.content_text}
              </pre>
            )}
          </div>
        )
      })}
    </div>
  )
}

const pillBtn = {
  padding: '4px 10px',
  borderRadius: 6,
  border: '1px solid rgba(0, 212, 255, 0.35)',
  background: 'transparent',
  color: 'rgba(0, 212, 255, 0.75)',
  fontFamily: 'monospace',
  fontSize: 10,
  letterSpacing: 1,
  cursor: 'pointer',
  textDecoration: 'none',
  display: 'inline-block',
}
