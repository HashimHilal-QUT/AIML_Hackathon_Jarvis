import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import MaterialUploader from '../components/MaterialUploader'
import MaterialList from '../components/MaterialList'
import SubjectChat from '../components/SubjectChat'
import { api } from '../lib/api'

const TABS = [
  { id: 'syllabus', label: 'Syllabus', kind: 'syllabus' },
  { id: 'module', label: 'Modules', kind: 'module' },
  { id: 'assignment', label: 'Assignments', kind: 'assignment' },
  { id: 'rubric', label: 'Rubrics', kind: 'rubric' },
  { id: 'file', label: 'Files', kind: 'file' },
  { id: 'note', label: 'Notes', kind: 'note' },
]

export default function SubjectDetailPage() {
  const { subjectId } = useParams()
  const [subject, setSubject] = useState(null)
  const [materials, setMaterials] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('syllabus')
  const [showChat, setShowChat] = useState(true)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.getSubject(subjectId)
      setSubject(res?.subject || null)
      setMaterials(res?.materials || [])
    } catch (e) {
      setError(e?.message || 'Failed to load subject')
    } finally {
      setLoading(false)
    }
  }, [subjectId])

  useEffect(() => {
    refresh()
  }, [refresh])

  const materialsForTab = useMemo(
    () => materials.filter((m) => m.kind === activeTab),
    [materials, activeTab]
  )

  const handleDelete = async (materialId) => {
    try {
      await api.deleteMaterial(subjectId, materialId)
      setMaterials((prev) => prev.filter((m) => m.id !== materialId))
    } catch (e) {
      alert(e?.message || 'Delete failed')
    }
  }

  const handleUploaded = (newMat) => {
    setMaterials((prev) => [newMat, ...prev])
  }

  if (loading && !subject) {
    return (
      <div style={{ color: 'rgba(230, 246, 255, 0.6)', fontFamily: 'monospace' }}>
        Loading…
      </div>
    )
  }
  if (error && !subject) {
    return (
      <div style={errorBox}>
        {error}
        <div style={{ marginTop: 12 }}>
          <Link to="/subjects" style={backLink}>
            ← back to subjects
          </Link>
        </div>
      </div>
    )
  }
  if (!subject) return null

  const color = subject.color || '#00d4ff'

  return (
    <div
      style={{
        maxWidth: 1400,
        margin: '0 auto',
        display: 'grid',
        gridTemplateColumns: showChat ? 'minmax(0, 1fr) 420px' : '1fr',
        gap: 24,
        alignItems: 'start',
      }}
    >
      <div>
        <Link to="/subjects" style={backLink}>
          ← all subjects
        </Link>
        <header
          style={{
            marginTop: 8,
            marginBottom: 24,
            padding: '18px 20px',
            borderRadius: 12,
            background:
              'linear-gradient(180deg, rgba(0, 30, 60, 0.65), rgba(0, 15, 30, 0.85))',
            border: `1px solid ${color}55`,
            boxShadow: `0 0 24px ${color}1f inset`,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              fontFamily: 'monospace',
              fontSize: 11,
              letterSpacing: 2,
              color,
            }}
          >
            <span
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                background: color,
                boxShadow: `0 0 8px ${color}`,
              }}
            />
            {subject.code || 'NO-CODE'}
            {subject.term ? ` · ${subject.term}` : ''}
          </div>
          <h1 style={{ fontSize: 28, margin: '6px 0 4px', fontWeight: 700 }}>
            {subject.name}
          </h1>
          {subject.description && (
            <p
              style={{
                color: 'rgba(230, 246, 255, 0.6)',
                fontSize: 13,
                lineHeight: 1.5,
                margin: 0,
              }}
            >
              {subject.description}
            </p>
          )}
          <div
            style={{
              marginTop: 12,
              display: 'flex',
              gap: 10,
              alignItems: 'center',
            }}
          >
            <button
              type="button"
              onClick={() => setShowChat((v) => !v)}
              style={{
                ...pillBtn,
                color: showChat ? '#00d4ff' : 'rgba(230, 246, 255, 0.75)',
                borderColor: showChat ? '#00d4ff' : 'rgba(230, 246, 255, 0.25)',
              }}
            >
              {showChat ? '✕ HIDE JARVIS' : '💬 ASK JARVIS'}
            </button>
          </div>
        </header>

        {/* Tabs */}
        <div
          style={{
            display: 'flex',
            gap: 4,
            borderBottom: '1px solid rgba(0, 212, 255, 0.2)',
            marginBottom: 20,
            overflowX: 'auto',
          }}
        >
          {TABS.map((t) => {
            const count = materials.filter((m) => m.kind === t.kind).length
            const active = activeTab === t.id
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => setActiveTab(t.id)}
                style={{
                  padding: '10px 18px',
                  background: active ? 'rgba(0, 212, 255, 0.12)' : 'transparent',
                  border: 'none',
                  borderBottom: active
                    ? '2px solid #00d4ff'
                    : '2px solid transparent',
                  color: active ? '#00d4ff' : 'rgba(230, 246, 255, 0.6)',
                  fontFamily: 'monospace',
                  fontSize: 12,
                  letterSpacing: 2,
                  cursor: 'pointer',
                  fontWeight: active ? 600 : 500,
                  whiteSpace: 'nowrap',
                }}
              >
                {t.label.toUpperCase()}
                {count > 0 && (
                  <span
                    style={{
                      marginLeft: 6,
                      fontSize: 10,
                      opacity: 0.6,
                    }}
                  >
                    ({count})
                  </span>
                )}
              </button>
            )
          })}
        </div>

        <MaterialUploader
          subjectId={subjectId}
          kind={activeTab}
          onUploaded={handleUploaded}
        />

        <div style={{ marginTop: 20 }}>
          <MaterialList
            materials={materialsForTab}
            onDelete={handleDelete}
          />
        </div>
      </div>

      {showChat && (
        <div
          style={{
            position: 'sticky',
            top: 16,
            minHeight: 560,
            maxHeight: 'calc(100vh - 64px)',
          }}
        >
          <SubjectChat subject={subject} materials={materials} />
        </div>
      )}
    </div>
  )
}

const errorBox = {
  padding: 16,
  borderRadius: 8,
  background: 'rgba(255, 80, 80, 0.1)',
  border: '1px solid rgba(255, 80, 80, 0.4)',
  color: 'rgba(255, 170, 170, 0.95)',
  fontSize: 13,
  fontFamily: 'monospace',
}
const backLink = {
  color: 'rgba(0, 212, 255, 0.75)',
  fontFamily: 'monospace',
  fontSize: 11,
  letterSpacing: 2,
  textDecoration: 'none',
}
const pillBtn = {
  padding: '6px 14px',
  borderRadius: 999,
  border: '1px solid rgba(0, 212, 255, 0.5)',
  background: 'transparent',
  fontFamily: 'monospace',
  fontSize: 11,
  letterSpacing: 2,
  cursor: 'pointer',
}
