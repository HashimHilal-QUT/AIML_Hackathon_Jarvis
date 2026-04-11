import { useState, useRef, useCallback } from 'react'

export default function useVoice() {
  const [isRecording, setIsRecording] = useState(false)
  const [amplitude, setAmplitude] = useState(0)
  const mediaRecorderRef = useRef(null)
  const audioContextRef = useRef(null)
  const analyserRef = useRef(null)
  const chunksRef = useRef([])
  const animationFrameRef = useRef(null)

  const startListening = useCallback(async () => {
    try {
      console.log('🎤 [START] Requesting microphone...')
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      console.log('✅ [GRANT] Microphone access granted')
      console.log(`📊 [STREAM] Audio tracks: ${stream.getAudioTracks().length}`)

      // Setup Web Audio API for amplitude analysis
      if (!audioContextRef.current) {
        // @ts-ignore - webkit fallback for older browsers
        const AudioContext = window.AudioContext || window.webkitAudioContext
        audioContextRef.current = new AudioContext()
      }

      const source = audioContextRef.current.createMediaStreamSource(stream)
      analyserRef.current = audioContextRef.current.createAnalyser()
      analyserRef.current.fftSize = 2048
      source.connect(analyserRef.current)

      // MediaRecorder setup
      console.log('🎙️ [SETUP] Creating MediaRecorder...')
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []
      console.log(`📋 [MIME] Using: ${mediaRecorder.mimeType}`)

      mediaRecorder.onerror = (e) => {
        console.error(`❌ [REC-ERROR] ${e.error}`)
      }

      mediaRecorder.ondataavailable = (e) => {
        console.log(`📦 [CHUNK] Received audio chunk: ${e.data.size} bytes`)
        chunksRef.current.push(e.data)
      }

      mediaRecorder.start()
      console.log('🔴 [REC] Recording started')
      setIsRecording(true)

      // Amplitude monitoring
      let ampFrames = 0
      const updateAmplitude = () => {
        if (!analyserRef.current) return
        ampFrames++

        const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
        analyserRef.current.getByteFrequencyData(dataArray)

        const average = dataArray.reduce((a, b) => a + b) / dataArray.length
        setAmplitude(average / 255)

        if (ampFrames === 1) {
          console.log(`📈 [AMP] Amplitude monitoring active`)
        }

        animationFrameRef.current = requestAnimationFrame(updateAmplitude)
      }
      updateAmplitude()
    } catch (err) {
      console.error('❌ [ERROR] Microphone error:', err.name, err.message)
    }
  }, [])

  const stopListening = useCallback(async () => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current) {
        resolve(null)
        return
      }

      mediaRecorderRef.current.onstop = async () => {
        console.log('⏹️ Recording stopped')
        setIsRecording(false)
        setAmplitude(0)

        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current)
        }

        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' })
        console.log(`📊 Audio blob created: ${audioBlob.size} bytes`)

        try {
          const formData = new FormData()
          formData.append('file', audioBlob, 'audio.webm')

          console.log('🔄 Sending to /api/voice/stt...')
          const response = await fetch('/api/voice/stt', {
            method: 'POST',
            body: formData,
          })

          if (response.ok) {
            const data = await response.json()
            console.log(`✅ Transcribed: "${data.text}"`)
            resolve(data.text)
          } else {
            console.error(`❌ STT request failed: ${response.status} ${response.statusText}`)
            resolve(null)
          }
        } catch (err) {
          console.error('❌ STT error:', err)
          resolve(null)
        }

        // Stop all tracks
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorderRef.current.stop()
    })
  }, [])

  const playAudio = useCallback(async (text) => {
    try {
      console.log(`🔊 Playing audio: "${text.slice(0, 50)}..."`)
      const response = await fetch('/api/voice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice: 'fable' })
      })

      if (response.ok) {
        const audioBlob = await response.blob()
        console.log(`✅ TTS generated: ${audioBlob.size} bytes`)
        const audioUrl = URL.createObjectURL(audioBlob)
        const audio = new Audio(audioUrl)
        audio.play()
        console.log('🎵 Playing audio...')
      }
    } catch (err) {
      console.error('TTS error:', err)
    }
  }, [])

  return {
    isRecording,
    amplitude,
    startListening,
    stopListening,
    playAudio
  }
}
