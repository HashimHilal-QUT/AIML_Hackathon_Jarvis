import { useEffect, useRef, useState } from 'react'
import useVoice from '../hooks/useVoice'
import useJarvis from '../hooks/useJarvis'
import useRealtime from '../hooks/useRealtime'
import useWakeWord from '../hooks/useWakeWord'

const PHRASES = [
  "Good evening, student.",
  "All systems are operating at peak efficiency.",
  "What can I assist you with today?",
  "Calendar synchronized. No conflicts detected.",
  "Your schedule is clear for the next session.",
  "Analyzing timetable data. Processing complete.",
  "Ready to help with your academic needs.",
  "Voice interface online and monitoring.",
]

export default function JarvisCanvas() {
  const canvasRef = useRef(null)
  const messagesEndRef = useRef(null)
  const [mode, setMode] = useState('speak')
  const [messages, setMessages] = useState([])
  const [uptime, setUptime] = useState(0)
  const [inputText, setInputText] = useState('')
  const stateRef = useRef({
    t: 0,
    speaking: true,
    speechAmp: 0,
    targetAmp: 0,
    wavePhase: 0,
    bars: new Array(32).fill(0),
    barTargets: new Array(32).fill(0),
    currentPhrase: PHRASES[0],
    charIndex: 0,
    typingActive: true,
    phraseTimer: 0,
    phraseIndex: 0,
    lastTyping: 0,
    lastBar: 0,
  })

  const {
    isRecording,
    amplitude,
    startListening,
    stopListening,
    playAudio,
  } = useVoice()

  const textBufferRef = useRef('')
  const lastPlayedRef = useRef('')

  const { sendToJarvis, isProcessing } = useJarvis({
    onResponse: (text) => {
      setMessages(prev => [...prev, { type: 'assistant', text }])

      // Stream audio: play every 1-2 sentences as they arrive
      textBufferRef.current = text
      const newText = text.slice(lastPlayedRef.current.length)

      // Check if we have a complete sentence (ends with . ! ?)
      if (newText.match(/[.!?]\s/)) {
        const lastSentenceEnd = Math.max(
          newText.lastIndexOf('.'),
          newText.lastIndexOf('!'),
          newText.lastIndexOf('?')
        )

        if (lastSentenceEnd > 0) {
          const textToPlay = text.slice(0, lastPlayedRef.current.length + lastSentenceEnd + 1).trim()
          const unplayedText = textToPlay.slice(lastPlayedRef.current.length)

          if (unplayedText.length > 3) {
            console.log(`🔊 Streaming: "${unplayedText.slice(0, 40)}..."`)
            playAudio(unplayedText)
            lastPlayedRef.current = textToPlay
          }
        }
      }
    },
    onDone: (text) => {
      // Play any remaining text
      const remaining = text.slice(lastPlayedRef.current.length).trim()
      if (remaining.length > 3) {
        console.log(`🔊 Final: "${remaining.slice(0, 40)}..."`)
        playAudio(remaining)
      }
      lastPlayedRef.current = ''
      textBufferRef.current = ''
    }
  })

  // Realtime voice-to-voice via OpenAI Realtime API (WebRTC, sub-300ms round-trip)
  const {
    isConnected: isRealtimeConnected,
    isConnecting: isRealtimeConnecting,
    isAssistantSpeaking: isRealtimeSpeaking,
    error: realtimeError,
    connect: realtimeConnect,
    disconnect: realtimeDisconnect,
  } = useRealtime()

  // While Realtime owns the mic, stop the legacy request/response pipeline so
  // the two don't fight over getUserMedia. When Realtime disconnects, leave the
  // old listener off — user can re-click VOICE to restart it.
  useEffect(() => {
    if (isRealtimeConnected) {
      stopListening()
    }
  }, [isRealtimeConnected, stopListening])

  const handleLiveClick = async () => {
    if (isRealtimeConnected || isRealtimeConnecting) {
      realtimeDisconnect()
      return
    }
    // If the legacy pipeline is holding the mic, release it before we request
    // a fresh getUserMedia for Realtime — otherwise Chrome rejects the 2nd
    // call with NotAllowedError.
    if (isRecording) {
      try {
        await stopListening()
      } catch {
        // fire-and-forget; we're about to reacquire anyway
      }
    }
    realtimeConnect()
  }

  // Wake word: passively listen for "Hey JARVIS" (and a few variants) and
  // auto-connect Realtime when detected. Disabled while a Realtime session is
  // already connecting/connected so the user's conversation doesn't re-trigger
  // a new connect. Also disabled while the legacy useVoice mic is recording
  // (both would call getUserMedia on the same device).
  const wakeEnabled = !isRealtimeConnected && !isRealtimeConnecting && !isRecording
  const {
    isListening: isWakeListening,
    isSupported: isWakeSupported,
    error: wakeError,
    lastTranscript: wakeTranscript,
  } = useWakeWord({
    enabled: wakeEnabled,
    verbose: false,
    onWake: async (phrase) => {
      console.log(`🪄 Wake phrase detected: "${phrase}" — connecting Realtime`)
      try {
        await realtimeConnect()
      } catch (err) {
        console.error('Realtime auto-connect from wake word failed:', err)
      }
    },
  })
  // Truncate interim transcript for HUD display
  const wakeTranscriptShort = (wakeTranscript || '').slice(-48)

  // === Diagnostics ===
  // Querying the Permissions API tells us whether the browser+OS even allow
  // mic access before we try to use it. Helps distinguish "user denied" from
  // "Web Speech API not supported" from "network blocked".
  // Diagnostic panel is hidden by default — click the small 🔬 chip in the
  // bottom-left to reveal it if something needs debugging.
  const [showDiagnostics, setShowDiagnostics] = useState(false)
  const [micPermissionState, setMicPermissionState] = useState('unknown')
  const [micTestResult, setMicTestResult] = useState(null)
  const [speechRecSupported, setSpeechRecSupported] = useState(null)
  const [browserLabel, setBrowserLabel] = useState('?')

  useEffect(() => {
    // Browser + API support detection
    const hasSR = !!(window.SpeechRecognition || window.webkitSpeechRecognition)
    setSpeechRecSupported(hasSR)

    const ua = navigator.userAgent
    let label = 'Unknown'
    if (/Edg\//.test(ua)) label = 'Edge'
    else if (/OPR\//.test(ua)) label = 'Opera'
    else if (/Chrome\//.test(ua) && !/Edg\//.test(ua)) label = 'Chrome'
    else if (/Safari\//.test(ua) && !/Chrome\//.test(ua)) label = 'Safari'
    else if (/Firefox\//.test(ua)) label = 'Firefox'
    if (/Atlas/i.test(ua)) label += ' (Atlas)'
    setBrowserLabel(label)

    // Permissions API (optional in Safari)
    if (navigator.permissions?.query) {
      navigator.permissions
        .query({ name: 'microphone' })
        .then((result) => {
          setMicPermissionState(result.state)
          result.onchange = () => setMicPermissionState(result.state)
        })
        .catch(() => setMicPermissionState('unsupported'))
    } else {
      setMicPermissionState('permissions-api-unavailable')
    }
  }, [])

  // Direct mic test — calls getUserMedia with no other mic consumers active,
  // so we can tell whether the browser+OS can grant mic access AT ALL.
  // Releases the stream immediately after success.
  const handleTestMic = async () => {
    setMicTestResult({ status: 'testing' })
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const tracks = stream.getAudioTracks()
      const label = tracks[0]?.label || '(no label)'
      // Release immediately
      tracks.forEach((t) => t.stop())
      setMicTestResult({ status: 'ok', label })
    } catch (err) {
      setMicTestResult({
        status: 'error',
        name: err?.name || 'Error',
        message: err?.message || String(err),
      })
    }
  }

  // NOTE: auto-start removed. The legacy useVoice pipeline acquired the mic
  // on mount, which conflicted with useRealtime / useWakeWord (both need
  // getUserMedia access) and caused "permission denied" when clicking LIVE.
  // The mic now stays free until the user explicitly starts a session by:
  //   - saying "Hey JARVIS" (handled by useWakeWord below), OR
  //   - tapping the ⚡ LIVE button (handled by handleLiveClick), OR
  //   - tapping the 🎙️ VOICE button (handled by handleMicClick, which calls
  //     startListening manually).

  useEffect(() => {
    // Update mode based on recording and processing state
    if (isRecording) {
      setMode('speak')
    } else if (isProcessing) {
      setMode('analyze')
    } else {
      setMode('speak')
    }
  }, [isRecording, isProcessing])

  // Auto-scroll messages to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Uptime counter
  useEffect(() => {
    const interval = setInterval(() => {
      setUptime(u => u + 1)
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    let W, H, cx, cy, R

    const resize = () => {
      W = canvas.width = window.innerWidth
      H = canvas.height = window.innerHeight
      cx = W / 2
      cy = H / 2
      R = Math.min(W, H) * 0.34
    }
    resize()
    window.addEventListener('resize', resize)

    const modeColor = (alpha) => {
      if (mode === 'alert') return `rgba(255,80,60,${alpha})`
      if (mode === 'analyze') return `rgba(80,220,160,${alpha})`
      return `rgba(0,200,255,${alpha})`
    }

    const goldColor = (alpha) => `rgba(245,166,35,${alpha})`

    const drawRings = () => {
      const spinSpeech = mode === 'speak' ? stateRef.current.speechAmp * 0.3 : 0

      ctx.beginPath()
      ctx.arc(cx, cy, R * 1.18, 0, Math.PI * 2)
      ctx.strokeStyle = modeColor(0.15)
      ctx.lineWidth = 0.5
      ctx.stroke()

      const tickCount = 72
      const tickR = R * 1.12
      const tr = stateRef.current.t * 0.3 + spinSpeech
      for (let i = 0; i < tickCount; i++) {
        const angle = (i / tickCount) * Math.PI * 2 + tr
        const major = i % 6 === 0
        const len = major ? 10 : 5
        const x1 = cx + Math.cos(angle) * tickR
        const y1 = cy + Math.sin(angle) * tickR
        const x2 = cx + Math.cos(angle) * (tickR + len)
        const y2 = cy + Math.sin(angle) * (tickR + len)
        ctx.beginPath()
        ctx.moveTo(x1, y1)
        ctx.lineTo(x2, y2)
        ctx.strokeStyle = modeColor(major ? 0.7 : 0.3)
        ctx.lineWidth = major ? 1.5 : 0.7
        ctx.stroke()
      }

      ctx.beginPath()
      ctx.arc(cx, cy, R * 1.06, 0, Math.PI * 2)
      ctx.strokeStyle = modeColor(0.9)
      ctx.lineWidth = 1.5
      ctx.stroke()

      ctx.beginPath()
      ctx.arc(cx, cy, R * 0.97, 0, Math.PI * 2)
      ctx.strokeStyle = modeColor(0.4)
      ctx.lineWidth = 0.7
      ctx.stroke()

      const ir = -stateRef.current.t * 0.5
      ctx.save()
      ctx.translate(cx, cy)
      ctx.rotate(ir)
      ctx.translate(-cx, -cy)
      ctx.beginPath()
      ctx.arc(cx, cy, R * 0.82, 0, Math.PI * 2)
      ctx.strokeStyle = modeColor(0.35)
      ctx.lineWidth = 0.6
      ctx.setLineDash([6, 4])
      ctx.stroke()
      ctx.setLineDash([])
      ctx.restore()

      const goldAmt = 0.25 + stateRef.current.speechAmp * 0.7
      ctx.beginPath()
      ctx.arc(cx, cy, R * 1.06, -Math.PI * 0.9, -Math.PI * 0.9 + Math.PI * 2 * goldAmt)
      ctx.strokeStyle = goldColor(0.85 + stateRef.current.speechAmp * 0.15)
      ctx.lineWidth = 4
      ctx.lineCap = 'round'
      ctx.stroke()
      ctx.lineCap = 'butt'

      ctx.beginPath()
      ctx.arc(cx, cy, R * 0.72, 0, Math.PI * 2)
      ctx.strokeStyle = modeColor(0.6)
      ctx.lineWidth = 1
      ctx.stroke()

      ctx.beginPath()
      ctx.arc(cx, cy, R * 0.71, 0, Math.PI * 2)
      const cfill = ctx.createRadialGradient(cx, cy, 0, cx, cy, R * 0.71)
      cfill.addColorStop(0, '#061828')
      cfill.addColorStop(1, '#020d1a')
      ctx.fillStyle = cfill
      ctx.fill()
    }

    const drawWaveform = () => {
      if (!stateRef.current.speaking && mode !== 'speak') return
      const wR = R * 0.6
      ctx.beginPath()
      const pts = 200
      for (let i = 0; i <= pts; i++) {
        const angle = (i / pts) * Math.PI * 2
        const freq1 = Math.sin(angle * 3 + stateRef.current.wavePhase * 2.1) * 0.5
        const freq2 = Math.sin(angle * 5 - stateRef.current.wavePhase * 1.3) * 0.3
        const freq3 = Math.sin(angle * 8 + stateRef.current.wavePhase * 3.7) * 0.2
        const noise = (freq1 + freq2 + freq3) * stateRef.current.speechAmp * wR * 0.18
        const r = wR + noise
        const x = cx + Math.cos(angle) * r
        const y = cy + Math.sin(angle) * r
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
      }
      ctx.closePath()
      ctx.strokeStyle = modeColor(0.45 + stateRef.current.speechAmp * 0.35)
      ctx.lineWidth = 1.2
      ctx.stroke()
    }

    const drawVoiceBars = () => {
      const barW = R * 0.018
      const barMaxH = R * 0.22
      const totalW = 32 * (barW + 2)
      const startX = cx - totalW / 2
      const barY = cy + R * 0.4

      for (let i = 0; i < 32; i++) {
        const bh = stateRef.current.bars[i] * barMaxH
        const x = startX + i * (barW + 2)
        const alpha = 0.4 + stateRef.current.bars[i] * 0.6
        ctx.fillStyle = modeColor(alpha)
        ctx.fillRect(x, barY - bh, barW, bh * 2)
      }

      ctx.fillStyle = modeColor(0.4)
      ctx.font = '9px Courier New'
      ctx.textAlign = 'center'
      ctx.fillText('VOICE WAVEFORM', cx, barY + barMaxH + 18)
    }

    const drawDataArcs = () => {
      const arcs = [
        { r: R * 0.92, start: 0.05, end: 0.28, alpha: 0.4, w: 1.5 },
        { r: R * 0.92, start: 0.35, end: 0.62, alpha: 0.3, w: 1 },
        { r: R * 0.92, start: 0.70, end: 0.92, alpha: 0.35, w: 1 },
      ]
      arcs.forEach(a => {
        const s = a.start * Math.PI * 2 - Math.PI / 2 + stateRef.current.t * 0.2
        const e = a.end * Math.PI * 2 - Math.PI / 2 + stateRef.current.t * 0.2
        ctx.beginPath()
        ctx.arc(cx, cy, a.r, s, e)
        ctx.strokeStyle = modeColor(a.alpha)
        ctx.lineWidth = a.w
        ctx.stroke()
      })

      const connR = R * 0.72
      const connEnd = R * 0.78
      ;[[0, -1], [1, 0], [0, 1], [-1, 0]].forEach(([dx, dy]) => {
        ctx.beginPath()
        ctx.moveTo(cx + dx * connR, cy + dy * connR)
        ctx.lineTo(cx + dx * connEnd, cy + dy * connEnd)
        ctx.strokeStyle = modeColor(0.5)
        ctx.lineWidth = 1
        ctx.stroke()
        ctx.beginPath()
        ctx.arc(cx + dx * connEnd, cy + dy * connEnd, 2, 0, Math.PI * 2)
        ctx.fillStyle = modeColor(0.9)
        ctx.fill()
      })
    }

    const drawCenter = () => {
      ctx.textAlign = 'center'
      const pulse = 0.85 + stateRef.current.speechAmp * 0.15 + Math.sin(stateRef.current.t * 2) * 0.05
      ctx.globalAlpha = pulse
      ctx.font = `bold ${Math.floor(R * 0.155)}px Courier New`
      ctx.fillStyle = '#ffffff'
      ctx.shadowColor = modeColor(1)
      ctx.shadowBlur = 12 + stateRef.current.speechAmp * 20
      ctx.fillText('J.A.R.V.I.S.', cx, cy + R * 0.06)
      ctx.shadowBlur = 0
      ctx.globalAlpha = 1

      const lw = R * 0.55
      ctx.strokeStyle = modeColor(0.35)
      ctx.lineWidth = 0.7
      ctx.beginPath()
      ctx.moveTo(cx - lw, cy - R * 0.1)
      ctx.lineTo(cx + lw, cy - R * 0.1)
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(cx - lw * 0.7, cy + R * 0.18)
      ctx.lineTo(cx + lw * 0.7, cy + R * 0.18)
      ctx.stroke()

      ctx.font = `${Math.floor(R * 0.065)}px Courier New`
      ctx.fillStyle = modeColor(0.55)
      ctx.fillText('SYSTEM ONLINE', cx, cy - R * 0.17)
      ctx.fillText('v7.3.2  //  STARK.TECH', cx, cy + R * 0.27)

      const dotY = cy - R * 0.32
      ctx.beginPath()
      ctx.arc(cx, dotY, 3 + stateRef.current.speechAmp * 3, 0, Math.PI * 2)
      ctx.fillStyle = modeColor(0.8 + Math.sin(stateRef.current.t * 4) * 0.2)
      ctx.fill()
    }

    const draw = () => {
      ctx.clearRect(0, 0, W, H)
      ctx.fillStyle = '#020d1a'
      ctx.fillRect(0, 0, W, H)

      ctx.strokeStyle = 'rgba(0,200,255,0.06)'
      ctx.lineWidth = 0.5
      const gs = 28
      for (let x = 0; x < W; x += gs) {
        ctx.beginPath()
        ctx.moveTo(x, 0)
        ctx.lineTo(x, H)
        ctx.stroke()
      }
      for (let y = 0; y < H; y += gs) {
        ctx.beginPath()
        ctx.moveTo(0, y)
        ctx.lineTo(W, y)
        ctx.stroke()
      }

      const grd = ctx.createRadialGradient(cx, cy, 0, cx, cy, R * 1.6)
      grd.addColorStop(0, modeColor(0.07))
      grd.addColorStop(1, 'transparent')
      ctx.fillStyle = grd
      ctx.fillRect(0, 0, W, H)

      if (mode === 'alert') {
        ctx.fillStyle = `rgba(255,60,40,${0.04 + 0.04 * Math.sin(stateRef.current.t * 8)})`
        ctx.fillRect(0, 0, W, H)
      }

      drawRings()
      drawWaveform()
      drawVoiceBars()
      drawDataArcs()
      drawCenter()
    }

    const loop = () => {
      requestAnimationFrame(loop)
      stateRef.current.t += 0.016
      stateRef.current.wavePhase += 0.04 + stateRef.current.speechAmp * 0.08

      if (mode === 'speak') {
        stateRef.current.targetAmp = stateRef.current.speaking
          ? 0.5 + Math.sin(stateRef.current.t * 1.7) * 0.3 + Math.sin(stateRef.current.t * 3.1) * 0.2
          : 0
      } else if (mode === 'alert') {
        stateRef.current.targetAmp = 0.7 + Math.sin(stateRef.current.t * 6) * 0.3
      } else if (mode === 'analyze') {
        stateRef.current.targetAmp = 0.2 + Math.sin(stateRef.current.t * 1.2) * 0.1
      } else {
        stateRef.current.targetAmp = 0.04
      }
      stateRef.current.speechAmp += (stateRef.current.targetAmp - stateRef.current.speechAmp) * 0.08

      // Update bars
      for (let i = 0; i < 32; i++) {
        if (mode === 'speak' && stateRef.current.speaking) {
          const center = (i - 16) / 16
          const env = Math.exp(-center * center * 2)
          stateRef.current.barTargets[i] = (0.1 + Math.random() * 0.9) * stateRef.current.speechAmp * env
        } else {
          stateRef.current.barTargets[i] = 0.05 + Math.sin(stateRef.current.t * 2 + i * 0.4) * 0.04
        }
        stateRef.current.bars[i] += (stateRef.current.barTargets[i] - stateRef.current.bars[i]) * 0.25
      }

      draw()
    }

    loop()

    return () => {
      window.removeEventListener('resize', resize)
    }
  }, [mode, playAudio])

  const handleMicClick = async () => {
    if (isRecording) {
      const transcript = await stopListening()
      if (transcript) {
        console.log(`👤 User said: "${transcript}"`)
        setMessages(prev => [...prev, { type: 'user', text: transcript }])
        setMode('analyze')
        // Use updated messages in callback
        const updatedMessages = [...messages, { type: 'user', text: transcript }]
        await sendToJarvis(transcript, updatedMessages)
        setMode('speak')
        // Auto-restart listening for continuous voice interaction
        setTimeout(() => startListening(), 500)
      } else {
        // If no transcript (user just clicked without speaking), restart
        startListening()
      }
    } else {
      startListening()
    }
  }

  const handleTextSubmit = async (e) => {
    e.preventDefault()
    if (!inputText.trim()) return

    const text = inputText.trim()
    console.log(`📝 Sending: "${text}"`)

    // Clear input immediately
    setInputText('')

    // Add user message to display
    setMessages(prev => [...prev, { type: 'user', text }])

    // Send to Claude (pass empty history - Claude will just respond)
    try {
      await sendToJarvis(text, [])
    } catch (err) {
      console.error('❌ Send failed:', err)
    }
  }

  return (
    <div style={{ width: '100vw', height: '100vh', overflow: 'hidden', background: '#020d1a' }}>
      <canvas ref={canvasRef} style={{ display: 'block' }} />

      {/* Chat Messages Display */}
      <div style={{
        position: 'absolute',
        bottom: '140px',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '80%',
        maxWidth: '600px',
        maxHeight: '280px',
        overflowY: 'auto',
        background: 'rgba(2, 13, 26, 0.85)',
        border: '1px solid #00c8ff44',
        borderRadius: '4px',
        padding: '16px',
        fontFamily: 'Courier New',
        fontSize: '12px',
        color: '#00c8ff',
        pointerEvents: 'none',
      }}>
        {messages.length === 0 ? (
          <div style={{ opacity: 0.5, textAlign: 'center' }}>
            🎤 Waiting for voice input...
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} style={{
              marginBottom: '12px',
              padding: '8px',
              background: msg.type === 'user' ? 'rgba(0, 200, 255, 0.08)' : 'rgba(0, 200, 255, 0.04)',
              borderLeft: `2px solid ${msg.type === 'user' ? '#00c8ff' : '#00c8ff66'}`,
              paddingLeft: '12px',
            }}>
              <div style={{ fontSize: '10px', opacity: 0.6, marginBottom: '4px' }}>
                {msg.type === 'user' ? '👤 YOU' : '🤖 JARVIS'}
              </div>
              <div style={{ lineHeight: '1.4', wordWrap: 'break-word' }}>
                {msg.text}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* HUD Corner Text */}
      <div style={{
        position: 'absolute',
        top: '16px',
        left: '20px',
        color: '#00c8ff88',
        fontSize: '9px',
        letterSpacing: '1.5px',
        lineHeight: '1.8',
        fontFamily: 'Courier New',
        pointerEvents: 'none',
      }}>
        SYS.CORE: ACTIVE<br />
        NEURAL.NET: 99.2%<br />
        UPTIME: {String(Math.floor(uptime / 3600)).padStart(2, '0')}:{String(Math.floor((uptime % 3600) / 60)).padStart(2, '0')}:{String(uptime % 60).padStart(2, '0')}
      </div>

      <div style={{
        position: 'absolute',
        top: '16px',
        right: '20px',
        color: '#00c8ff88',
        fontSize: '9px',
        letterSpacing: '1.5px',
        lineHeight: '1.8',
        fontFamily: 'Courier New',
        textAlign: 'right',
        pointerEvents: 'none',
      }}>
        MODE: {isRealtimeConnected ? 'LIVE' : isRecording ? 'LISTENING' : isProcessing ? 'ANALYZING' : 'STANDBY'}<br />
        STATUS: {isRealtimeConnected ? '🟢 LIVE' : isRecording ? '🎤 ACTIVE' : '✓ READY'}<br />
        WAKE: {isWakeListening ? '● LISTENING' : !isWakeSupported ? '◌ UNSUPPORTED' : wakeError === 'not-allowed' ? '✗ MIC BLOCKED' : '◌ IDLE'}
      </div>

      <div style={{
        position: 'absolute',
        bottom: '70px',
        left: '20px',
        color: '#00c8ff88',
        fontSize: '9px',
        letterSpacing: '1.5px',
        lineHeight: '1.8',
        fontFamily: 'Courier New',
        pointerEvents: 'none',
      }}>
        PWR: ████████ 94%<br />
        TEMP: 36.4°C
      </div>

      <div style={{
        position: 'absolute',
        bottom: '70px',
        right: '20px',
        color: '#00c8ff88',
        fontSize: '9px',
        letterSpacing: '1.5px',
        lineHeight: '1.8',
        fontFamily: 'Courier New',
        textAlign: 'right',
        pointerEvents: 'none',
      }}>
        STARK.TECH v7.3<br />
        AI.CORE: READY
      </div>

      {/* Diagnostics toggle chip (bottom-left, always available) */}
      <button
        type="button"
        onClick={() => setShowDiagnostics((v) => !v)}
        title="Toggle diagnostics"
        style={{
          position: 'absolute',
          bottom: '16px',
          left: '20px',
          zIndex: 101,
          background: showDiagnostics ? '#f5a62322' : 'rgba(2, 13, 26, 0.6)',
          border: `1px solid ${showDiagnostics ? '#f5a623' : '#f5a62344'}`,
          color: showDiagnostics ? '#f5a623' : '#f5a62388',
          fontFamily: 'Courier New',
          fontSize: '10px',
          letterSpacing: '1px',
          padding: '6px 10px',
          borderRadius: '3px',
          cursor: 'pointer',
        }}
      >
        🔬 {showDiagnostics ? 'HIDE DIAG' : 'DIAG'}
      </button>

      {/* ===== DIAGNOSTIC PANEL (hidden by default) ===== */}
      {showDiagnostics && (
      <div
        style={{
          position: 'absolute',
          top: '16px',
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(2, 13, 26, 0.92)',
          border: '1px solid #f5a62388',
          borderRadius: '4px',
          padding: '10px 14px',
          color: '#e6f6ff',
          fontFamily: 'Courier New',
          fontSize: '11px',
          letterSpacing: '0.5px',
          zIndex: 100,
          maxWidth: '560px',
          pointerEvents: 'all',
          boxShadow: '0 0 16px rgba(245, 166, 35, 0.15)',
        }}
      >
        <div
          style={{
            color: '#f5a623',
            fontWeight: 'bold',
            marginBottom: '6px',
            letterSpacing: '2px',
          }}
        >
          🔬 JARVIS DIAGNOSTICS
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '2px 8px', fontSize: '10px' }}>
          <span style={{ opacity: 0.55 }}>BROWSER:</span>
          <span>{browserLabel}</span>
          <span style={{ opacity: 0.55 }}>SPEECH API:</span>
          <span style={{ color: speechRecSupported ? '#7fffa0' : '#ff7070' }}>
            {speechRecSupported === null ? 'detecting…' : speechRecSupported ? '✓ supported' : '✗ NOT SUPPORTED'}
          </span>
          <span style={{ opacity: 0.55 }}>MIC PERMISSION:</span>
          <span
            style={{
              color:
                micPermissionState === 'granted'
                  ? '#7fffa0'
                  : micPermissionState === 'denied'
                    ? '#ff7070'
                    : '#f5a623',
            }}
          >
            {micPermissionState}
          </span>
          <span style={{ opacity: 0.55 }}>WAKE LISTENING:</span>
          <span style={{ color: isWakeListening ? '#7fffa0' : '#ff7070' }}>
            {isWakeListening ? '● yes' : '◌ no'}
            {wakeError ? ` (err: ${wakeError})` : ''}
          </span>
          <span style={{ opacity: 0.55 }}>LAST HEARD:</span>
          <span
            style={{
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              fontStyle: 'italic',
              opacity: wakeTranscript ? 0.95 : 0.4,
            }}
          >
            {wakeTranscript || '(nothing yet)'}
          </span>
          <span style={{ opacity: 0.55 }}>REALTIME:</span>
          <span
            style={{
              color: isRealtimeConnected
                ? '#7fffa0'
                : isRealtimeConnecting
                  ? '#f5a623'
                  : realtimeError
                    ? '#ff7070'
                    : '#aaa',
            }}
          >
            {isRealtimeConnecting
              ? 'connecting…'
              : isRealtimeConnected
                ? 'connected'
                : realtimeError
                  ? `error: ${realtimeError.slice(0, 60)}`
                  : 'disconnected'}
          </span>
          {micTestResult && (
            <>
              <span style={{ opacity: 0.55 }}>MIC TEST:</span>
              <span
                style={{
                  color:
                    micTestResult.status === 'ok'
                      ? '#7fffa0'
                      : micTestResult.status === 'error'
                        ? '#ff7070'
                        : '#f5a623',
                }}
              >
                {micTestResult.status === 'ok'
                  ? `✓ got mic: ${micTestResult.label}`
                  : micTestResult.status === 'error'
                    ? `✗ ${micTestResult.name}: ${micTestResult.message}`
                    : 'testing…'}
              </span>
            </>
          )}
        </div>
        <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
          <button
            type="button"
            onClick={handleTestMic}
            style={{
              fontFamily: 'Courier New',
              fontSize: '10px',
              padding: '4px 10px',
              background: '#f5a62322',
              border: '1px solid #f5a62388',
              color: '#f5a623',
              cursor: 'pointer',
              letterSpacing: '1px',
            }}
          >
            TEST MIC
          </button>
          <button
            type="button"
            onClick={() => realtimeConnect()}
            style={{
              fontFamily: 'Courier New',
              fontSize: '10px',
              padding: '4px 10px',
              background: '#00c8ff22',
              border: '1px solid #00c8ff88',
              color: '#00c8ff',
              cursor: 'pointer',
              letterSpacing: '1px',
            }}
          >
            FORCE CONNECT
          </button>
          <button
            type="button"
            onClick={() => {
              // eslint-disable-next-line no-alert
              const text = `Browser: ${browserLabel}
UA: ${navigator.userAgent}
SpeechRec: ${speechRecSupported}
Mic permission: ${micPermissionState}
Wake listening: ${isWakeListening}
Wake error: ${wakeError || 'none'}
Last transcript: ${wakeTranscript || 'none'}
Realtime state: ${isRealtimeConnected ? 'connected' : isRealtimeConnecting ? 'connecting' : 'disconnected'}
Realtime error: ${realtimeError || 'none'}
Mic test: ${micTestResult ? JSON.stringify(micTestResult) : 'not run'}`
              navigator.clipboard?.writeText(text).catch(() => {})
              console.log('[diag]', text)
            }}
            style={{
              fontFamily: 'Courier New',
              fontSize: '10px',
              padding: '4px 10px',
              background: 'transparent',
              border: '1px solid #e6f6ff44',
              color: '#e6f6ff',
              cursor: 'pointer',
              letterSpacing: '1px',
            }}
          >
            COPY DIAG
          </button>
        </div>
      </div>
      )}

      {/* Live wake-word transcript (debug visibility) */}
      {isWakeListening && wakeTranscriptShort && (
        <div
          style={{
            position: 'absolute',
            top: '85px',
            left: '50%',
            transform: 'translateX(-50%)',
            color: '#00c8ff',
            fontSize: '10px',
            letterSpacing: '1px',
            fontFamily: 'Courier New',
            padding: '4px 10px',
            background: 'rgba(0, 200, 255, 0.08)',
            border: '1px solid #00c8ff44',
            borderRadius: '3px',
            maxWidth: '80%',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            pointerEvents: 'none',
            opacity: 0.85,
          }}
        >
          🎙 heard: "{wakeTranscriptShort}"
        </div>
      )}

      {/* Status Text */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translateX(-50%)',
        color: isRealtimeConnected ? '#f5a623' : '#00c8ff',
        fontSize: '11px',
        letterSpacing: '3px',
        textTransform: 'uppercase',
        marginTop: '12px',
        opacity: 0.85,
        fontFamily: 'Courier New',
        pointerEvents: 'none',
        textShadow: isRealtimeConnected ? '0 0 12px #f5a62366' : 'none',
      }}>
        {isRealtimeSpeaking
          ? '🔊 SAGE SPEAKING…'
          : isRealtimeConnected
            ? '🟢 LIVE // SAGE READY — SAY ANYTHING'
            : isRealtimeConnecting
              ? '⏳ CONNECTING TO SAGE…'
              : isRecording
                ? '🎤 LISTENING…'
                : isWakeListening
                  ? "🪄 SAY 'HEY JARVIS' OR TAP LIVE"
                  : !isWakeSupported
                    ? 'TAP LIVE TO START'
                    : wakeError === 'not-allowed'
                      ? '⚠ MIC PERMISSION REQUIRED'
                      : 'SYSTEM ONLINE'}
      </div>

      {/* Voice & Text Input Controls */}
      <div style={{
        position: 'absolute',
        bottom: '40px',
        left: '50%',
        transform: 'translateX(-50%)',
        pointerEvents: 'all',
        display: 'flex',
        gap: '12px',
        alignItems: 'center',
      }}>
        <button
          onClick={handleLiveClick}
          title={realtimeError ? `Realtime error: ${realtimeError}` : 'OpenAI Realtime API — sub-300ms voice-to-voice'}
          style={{
            background: isRealtimeConnected
              ? (isRealtimeSpeaking ? '#f5a62333' : '#f5a62322')
              : 'transparent',
            border: `2px solid ${
              isRealtimeConnected ? '#f5a623' : isRealtimeConnecting ? '#f5a62388' : '#f5a62366'
            }`,
            color: '#f5a623',
            fontFamily: 'Courier New',
            fontSize: '12px',
            letterSpacing: '3px',
            padding: '12px 28px',
            cursor: 'pointer',
            textTransform: 'uppercase',
            boxShadow: isRealtimeConnected
              ? '0 0 20px #f5a62366, inset 0 0 10px #f5a62322'
              : '0 0 10px #f5a62333',
            transition: 'all 0.3s ease',
            fontWeight: 'bold',
          }}
        >
          {isRealtimeConnecting
            ? '⏳ CONNECTING'
            : isRealtimeConnected
              ? isRealtimeSpeaking
                ? '🔊 SPEAKING'
                : '🟢 LIVE — TAP TO END'
              : '⚡ LIVE'}
        </button>

        <button
          onClick={handleMicClick}
          style={{
            background: isRecording ? '#00c8ff33' : 'transparent',
            border: `2px solid ${isRecording ? '#00c8ff' : '#00c8ff66'}`,
            color: '#00c8ff',
            fontFamily: 'Courier New',
            fontSize: '12px',
            letterSpacing: '3px',
            padding: '12px 28px',
            cursor: 'pointer',
            textTransform: 'uppercase',
            boxShadow: isRecording ? '0 0 20px #00c8ff66, inset 0 0 10px #00c8ff22' : '0 0 10px #00c8ff33',
            transition: 'all 0.3s ease',
            fontWeight: 'bold',
          }}
        >
          {isRecording ? '🎤 LISTENING' : '🎙️ VOICE'}
        </button>

        <form onSubmit={handleTextSubmit} style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="or type here..."
            style={{
              background: 'rgba(0, 200, 255, 0.08)',
              border: '1px solid #00c8ff66',
              color: '#00c8ff',
              fontFamily: 'Courier New',
              fontSize: '11px',
              padding: '10px 12px',
              borderRadius: '3px',
              outline: 'none',
              width: '200px',
              transition: 'all 0.2s ease',
            }}
            onFocus={(e) => e.target.style.borderColor = '#00c8ff'}
            onBlur={(e) => e.target.style.borderColor = '#00c8ff66'}
          />
          <button
            type="submit"
            style={{
              background: inputText.trim() ? '#00c8ff22' : 'transparent',
              border: `1px solid ${inputText.trim() ? '#00c8ff' : '#00c8ff44'}`,
              color: '#00c8ff',
              fontFamily: 'Courier New',
              fontSize: '10px',
              letterSpacing: '2px',
              padding: '10px 16px',
              cursor: inputText.trim() ? 'pointer' : 'default',
              textTransform: 'uppercase',
              opacity: inputText.trim() ? 1 : 0.5,
            }}
            disabled={!inputText.trim()}
          >
            SEND
          </button>
        </form>
      </div>

      {/* Uptime updater - using useEffect instead of script tag */}
    </div>
  )
}
