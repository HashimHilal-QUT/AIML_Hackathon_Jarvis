import { useCallback, useEffect, useRef, useState } from 'react'
import { supabase } from '../lib/supabase'

/**
 * Chat pane for a single subject. Streams responses from /api/chat with
 * subject_id so the backend can inject the full subject dossier (syllabus +
 * modules + rubrics + extracted PDF text) into Claude's system prompt.
 *
 * Uses the same SSE event contract as useJarvis.js — 'delta' chunks for
 * streaming text and a final 'done' event.
 */
export default function SubjectChat({ subject, materials }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState(null)
  const endRef = useRef(null)

  // Scroll to bottom on new messages
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const materialCount = materials?.length || 0

  const send = useCallback(
    async (text) => {
      const msg = text?.trim()
      if (!msg) return
      setError(null)

      // Append user turn + placeholder assistant turn
      setMessages((prev) => [
        ...prev,
        { role: 'user', content: msg },
        { role: 'assistant', content: '', pending: true },
      ])
      setInput('')
      setStreaming(true)

      const history = messages.map((m) => ({ role: m.role, content: m.content }))

      try {
        const {
          data: { session },
        } = await supabase.auth.getSession()

        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(session?.access_token
              ? { Authorization: `Bearer ${session.access_token}` }
              : {}),
          },
          body: JSON.stringify({
            message: msg,
            history,
            subject_id: subject.id,
          }),
        })

        if (!res.ok) {
          throw new Error(`Chat failed with ${res.status}`)
        }

        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let assistantText = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            try {
              const evt = JSON.parse(line.slice(6))
              if (evt.type === 'delta') {
                assistantText += evt.text || ''
                setMessages((prev) => {
                  const copy = [...prev]
                  const last = copy[copy.length - 1]
                  if (last?.role === 'assistant') {
                    copy[copy.length - 1] = {
                      ...last,
                      content: assistantText,
                      pending: false,
                    }
                  }
                  return copy
                })
              } else if (evt.type === 'error') {
                throw new Error(evt.text || 'error')
              }
            } catch (parseErr) {
              // Skip partial/invalid lines
            }
          }
        }

        // Mark last message as finalised
        setMessages((prev) => {
          const copy = [...prev]
          const last = copy[copy.length - 1]
          if (last?.role === 'assistant') {
            copy[copy.length - 1] = { ...last, pending: false }
          }
          return copy
        })
      } catch (e) {
        setError(e?.message || 'Chat failed')
        setMessages((prev) => {
          const copy = [...prev]
          if (copy[copy.length - 1]?.role === 'assistant') {
            copy[copy.length - 1] = {
              role: 'assistant',
              content: `⚠ ${e?.message || 'chat failed'}`,
              pending: false,
            }
          }
          return copy
        })
      } finally {
        setStreaming(false)
      }
    },
    [messages, subject.id]
  )

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!streaming) send(input)
  }

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        minHeight: 560,
        maxHeight: 'calc(100vh - 64px)',
        background: 'rgba(0, 15, 30, 0.85)',
        border: '1px solid rgba(0, 212, 255, 0.3)',
        borderRadius: 12,
        overflow: 'hidden',
      }}
    >
      <header
        style={{
          padding: '14px 16px',
          borderBottom: '1px solid rgba(0, 212, 255, 0.18)',
          background: 'rgba(0, 30, 60, 0.55)',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            fontFamily: 'monospace',
            fontSize: 10,
            letterSpacing: 3,
            color: 'rgba(0, 212, 255, 0.6)',
          }}
        >
          JARVIS // COURSE HELPER
        </div>
        <div style={{ fontSize: 14, fontWeight: 600, marginTop: 2 }}>
          {subject.name}
        </div>
        <div
          style={{
            fontSize: 10,
            fontFamily: 'monospace',
            color: 'rgba(230, 246, 255, 0.45)',
            marginTop: 2,
          }}
        >
          {materialCount} material{materialCount === 1 ? '' : 's'} loaded
        </div>
      </header>

      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 14,
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
        }}
      >
        {!messages.length && (
          <div
            style={{
              fontSize: 12,
              color: 'rgba(230, 246, 255, 0.5)',
              lineHeight: 1.6,
              padding: '10px 12px',
              background: 'rgba(0, 212, 255, 0.05)',
              border: '1px solid rgba(0, 212, 255, 0.15)',
              borderRadius: 8,
            }}
          >
            Ask Jarvis anything about <strong>{subject.name}</strong>. He has
            access to your syllabus, modules, assignment rubrics, and any files
            you've uploaded.
            <ul
              style={{
                margin: '8px 0 0 18px',
                padding: 0,
                fontSize: 11,
                color: 'rgba(230, 246, 255, 0.55)',
              }}
            >
              <li>"What topics are covered in this course?"</li>
              <li>"Explain the assignment 2 rubric in simple terms"</li>
              <li>"What's the weight of the final exam?"</li>
              <li>"Summarise module 3 in three bullet points"</li>
            </ul>
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: m.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <div
              style={{
                fontSize: 9,
                fontFamily: 'monospace',
                letterSpacing: 2,
                color: 'rgba(230, 246, 255, 0.4)',
                marginBottom: 3,
              }}
            >
              {m.role === 'user' ? 'YOU' : 'JARVIS'}
            </div>
            <div
              style={{
                maxWidth: '88%',
                padding: '10px 12px',
                borderRadius: 10,
                background:
                  m.role === 'user'
                    ? 'rgba(0, 212, 255, 0.15)'
                    : 'rgba(0, 20, 40, 0.7)',
                border:
                  m.role === 'user'
                    ? '1px solid rgba(0, 212, 255, 0.35)'
                    : '1px solid rgba(245, 166, 35, 0.3)',
                color: '#e6f6ff',
                fontSize: 13,
                lineHeight: 1.55,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {m.content || (m.pending ? '…' : '')}
            </div>
          </div>
        ))}
        <div ref={endRef} />
      </div>

      {error && (
        <div
          style={{
            padding: '8px 14px',
            fontSize: 11,
            fontFamily: 'monospace',
            color: 'rgba(255, 170, 170, 0.95)',
            background: 'rgba(255, 80, 80, 0.08)',
            borderTop: '1px solid rgba(255, 80, 80, 0.3)',
            flexShrink: 0,
          }}
        >
          {error}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        style={{
          padding: 12,
          borderTop: '1px solid rgba(0, 212, 255, 0.2)',
          display: 'flex',
          gap: 8,
          flexShrink: 0,
          background: 'rgba(0, 15, 30, 0.95)',
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={streaming}
          placeholder={
            streaming
              ? 'Jarvis is replying…'
              : `Ask about ${subject.name}…`
          }
          style={{
            flex: 1,
            padding: '10px 12px',
            borderRadius: 8,
            border: '1px solid rgba(0, 212, 255, 0.3)',
            background: 'rgba(0, 10, 25, 0.65)',
            color: '#e6f6ff',
            fontSize: 13,
            outline: 'none',
          }}
        />
        <button
          type="submit"
          disabled={streaming || !input.trim()}
          style={{
            padding: '10px 16px',
            borderRadius: 8,
            border: '1px solid rgba(0, 212, 255, 0.65)',
            background: streaming
              ? 'rgba(0, 212, 255, 0.08)'
              : 'rgba(0, 212, 255, 0.18)',
            color: '#00d4ff',
            fontFamily: 'monospace',
            fontSize: 11,
            letterSpacing: 2,
            cursor: streaming || !input.trim() ? 'default' : 'pointer',
            opacity: streaming || !input.trim() ? 0.5 : 1,
          }}
        >
          {streaming ? '...' : 'SEND'}
        </button>
      </form>
    </div>
  )
}
