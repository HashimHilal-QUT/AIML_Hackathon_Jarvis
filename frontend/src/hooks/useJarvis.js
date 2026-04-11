import { useState, useCallback } from 'react'
import { supabase } from '../lib/supabase'

export default function useJarvis({ onResponse, onEvents, onDone }) {
  const [isProcessing, setIsProcessing] = useState(false)

  const sendToJarvis = useCallback(async (message, previousMessages = []) => {
    console.log(`💬 Sending to Claude: "${message}"`)
    console.log(`📝 Message history length: ${previousMessages.length}`)
    setIsProcessing(true)

    try {
      // Attach the Supabase session token so chat.py's calendar tools can
      // scope queries to the signed-in user. If not signed in, the backend
      // falls back gracefully (tools return not_signed_in and Claude tells
      // the user to sign in on the admin panel).
      const {
        data: { session },
      } = await supabase.auth.getSession()

      const headers = { 'Content-Type': 'application/json' }
      if (session?.access_token) {
        headers.Authorization = `Bearer ${session.access_token}`
      }

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message,
          history: previousMessages
        })
      })

      if (!response.ok) throw new Error('Chat request failed')

      console.log('✅ Chat request sent, receiving SSE stream...')
      // Handle SSE stream
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullText = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.type === 'delta') {
                fullText += data.text
                console.log(`📨 Received delta: "${data.text.slice(0, 30)}..."`)
              } else if (data.type === 'done') {
                console.log(`✅ Response complete: ${fullText.length} chars`)
                onResponse?.(fullText)
                onDone?.(fullText)
                if (data.events) {
                  onEvents?.(data.events)
                }
              }
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }
    } catch (err) {
      console.error('Chat error:', err)
      onResponse?.('Unable to process request. Please try again.')
    } finally {
      setIsProcessing(false)
    }
  }, [onResponse, onEvents])

  return {
    sendToJarvis,
    isProcessing
  }
}
