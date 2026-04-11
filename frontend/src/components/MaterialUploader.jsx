import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'

/**
 * Unified uploader for one material kind (syllabus / module / rubric / ...).
 * Accepts:
 *   - typed / pasted plain text
 *   - pasted screenshot (ctrl/cmd+V with an image on the clipboard)
 *   - drag-dropped files
 *   - click-to-choose files via the file picker
 */
export default function MaterialUploader({ subjectId, kind, onUploaded }) {
  const [textValue, setTextValue] = useState('')
  const [title, setTitle] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [dragging, setDragging] = useState(false)
  const fileInputRef = useRef(null)
  const dropZoneRef = useRef(null)

  // Clear fields when the active tab changes
  useEffect(() => {
    setTextValue('')
    setTitle('')
    setError(null)
    setSuccess(null)
  }, [kind])

  const uploadFile = useCallback(
    async (file) => {
      if (!file) return
      setBusy(true)
      setError(null)
      setSuccess(null)
      try {
        const created = await api.uploadMaterialFile(subjectId, {
          file,
          kind,
          title: title || undefined,
        })
        onUploaded(created)
        setTitle('')
        setSuccess(`Uploaded ${file.name}`)
        setTimeout(() => setSuccess(null), 3000)
      } catch (e) {
        setError(e?.message || 'Upload failed')
      } finally {
        setBusy(false)
      }
    },
    [subjectId, kind, title, onUploaded]
  )

  const uploadText = async () => {
    const trimmed = textValue.trim()
    if (!trimmed) {
      setError('Paste or type some text first.')
      return
    }
    setBusy(true)
    setError(null)
    setSuccess(null)
    try {
      const created = await api.createMaterialText(subjectId, {
        kind,
        title: title || undefined,
        content_text: trimmed,
      })
      onUploaded(created)
      setTextValue('')
      setTitle('')
      setSuccess('Saved')
      setTimeout(() => setSuccess(null), 2500)
    } catch (e) {
      setError(e?.message || 'Save failed')
    } finally {
      setBusy(false)
    }
  }

  // Paste handler — extracts images from the clipboard
  const handlePaste = useCallback(
    (e) => {
      const items = e.clipboardData?.items || []
      for (const item of items) {
        if (item.type?.startsWith('image/')) {
          e.preventDefault()
          const blob = item.getAsFile()
          if (blob) {
            const ts = new Date().toISOString().replace(/[:.]/g, '-')
            const file = new File([blob], `pasted-${ts}.png`, {
              type: blob.type || 'image/png',
            })
            uploadFile(file)
          }
          return
        }
      }
      // Otherwise, allow normal text paste into the textarea
    },
    [uploadFile]
  )

  // Drag & drop
  useEffect(() => {
    const el = dropZoneRef.current
    if (!el) return
    const onOver = (e) => {
      e.preventDefault()
      setDragging(true)
    }
    const onLeave = () => setDragging(false)
    const onDrop = (e) => {
      e.preventDefault()
      setDragging(false)
      const file = e.dataTransfer?.files?.[0]
      if (file) uploadFile(file)
    }
    el.addEventListener('dragover', onOver)
    el.addEventListener('dragleave', onLeave)
    el.addEventListener('drop', onDrop)
    return () => {
      el.removeEventListener('dragover', onOver)
      el.removeEventListener('dragleave', onLeave)
      el.removeEventListener('drop', onDrop)
    }
  }, [uploadFile])

  return (
    <div
      ref={dropZoneRef}
      onPaste={handlePaste}
      style={{
        padding: 16,
        borderRadius: 12,
        background: dragging
          ? 'rgba(0, 212, 255, 0.12)'
          : 'rgba(0, 20, 40, 0.5)',
        border: dragging
          ? '2px dashed rgba(0, 212, 255, 0.7)'
          : '1px dashed rgba(0, 212, 255, 0.3)',
        transition: 'all 120ms ease-out',
      }}
    >
      <div
        style={{
          fontFamily: 'monospace',
          fontSize: 10,
          letterSpacing: 2,
          color: 'rgba(0, 212, 255, 0.55)',
          marginBottom: 8,
        }}
      >
        ADD {kind.toUpperCase()}
      </div>

      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Optional title (e.g. Week 3 Lecture, Assignment 2 Rubric)"
        style={inputStyle}
      />

      <textarea
        value={textValue}
        onChange={(e) => setTextValue(e.target.value)}
        placeholder={`Paste the ${kind} text here, drop a file, or paste a screenshot (Cmd+V). PDFs and images are OCR'd automatically.`}
        style={{
          ...inputStyle,
          marginTop: 10,
          minHeight: 120,
          fontFamily: 'inherit',
          resize: 'vertical',
        }}
      />

      <div
        style={{
          display: 'flex',
          gap: 10,
          marginTop: 10,
          alignItems: 'center',
          flexWrap: 'wrap',
        }}
      >
        <button
          type="button"
          onClick={uploadText}
          disabled={busy || !textValue.trim()}
          style={{
            ...primaryBtn,
            opacity: busy || !textValue.trim() ? 0.5 : 1,
          }}
        >
          {busy ? 'SAVING…' : '+ SAVE TEXT'}
        </button>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={busy}
          style={secondaryBtn}
        >
          📎 UPLOAD FILE
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf,image/*,text/plain,text/markdown"
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) uploadFile(f)
            if (fileInputRef.current) fileInputRef.current.value = ''
          }}
          style={{ display: 'none' }}
        />
        <span
          style={{
            fontSize: 11,
            color: 'rgba(230, 246, 255, 0.4)',
            fontFamily: 'monospace',
          }}
        >
          or drop / paste a screenshot
        </span>
      </div>

      {error && <div style={errorBox}>{error}</div>}
      {success && <div style={successBox}>{success}</div>}
    </div>
  )
}

const primaryBtn = {
  padding: '9px 16px',
  borderRadius: 8,
  border: '1px solid rgba(0, 212, 255, 0.65)',
  background: 'rgba(0, 212, 255, 0.18)',
  color: '#00d4ff',
  fontFamily: 'monospace',
  fontSize: 11,
  letterSpacing: 2,
  cursor: 'pointer',
  fontWeight: 600,
}
const secondaryBtn = {
  padding: '9px 16px',
  borderRadius: 8,
  border: '1px solid rgba(245, 166, 35, 0.55)',
  background: 'rgba(245, 166, 35, 0.1)',
  color: '#f5a623',
  fontFamily: 'monospace',
  fontSize: 11,
  letterSpacing: 2,
  cursor: 'pointer',
  fontWeight: 600,
}
const inputStyle = {
  width: '100%',
  padding: '10px 12px',
  borderRadius: 8,
  border: '1px solid rgba(0, 212, 255, 0.25)',
  background: 'rgba(0, 10, 25, 0.65)',
  color: '#e6f6ff',
  fontSize: 13,
  outline: 'none',
  boxSizing: 'border-box',
}
const errorBox = {
  marginTop: 10,
  padding: '8px 10px',
  borderRadius: 6,
  background: 'rgba(255, 80, 80, 0.1)',
  border: '1px solid rgba(255, 80, 80, 0.35)',
  color: 'rgba(255, 170, 170, 0.95)',
  fontSize: 11,
  fontFamily: 'monospace',
}
const successBox = {
  marginTop: 10,
  padding: '8px 10px',
  borderRadius: 6,
  background: 'rgba(127, 255, 160, 0.08)',
  border: '1px solid rgba(127, 255, 160, 0.35)',
  color: 'rgba(127, 255, 160, 0.95)',
  fontSize: 11,
  fontFamily: 'monospace',
}
