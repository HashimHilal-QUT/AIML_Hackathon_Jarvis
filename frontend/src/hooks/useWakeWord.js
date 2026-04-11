/**
 * useWakeWord — passive "Hey JARVIS" wake-phrase detector using the Web Speech
 * API (webkitSpeechRecognition / SpeechRecognition).
 *
 * Coexists with getUserMedia: Chrome's SpeechRecognition does use the mic but
 * releases it cleanly on `onend`, so the hook's onWake() fires from onend +
 * a tiny 100ms tick to guarantee the mic is free before the caller tries to
 * reacquire it (e.g. for WebRTC).
 *
 * Browser support: Chrome / Edge desktop (full), Safari (partial, flaky),
 * Firefox (none). `isSupported` exposes the result of feature detection.
 *
 * Debugging: set `verbose: true` (default) to get `[wakeword] …` logs for
 * every recognition lifecycle event and every transcript chunk. Look in the
 * browser devtools console if the wake word doesn't fire.
 */
import { useCallback, useEffect, useRef, useState } from 'react'

// Regex that catches the most common transcriptions of "Hey JARVIS" /
// "Hi Jarvis" / "OK Jarvis" / just "Jarvis". Google Speech notoriously
// transcribes "jarvis" as "jervis", "javis", "jarvice", "charvis", or even
// "charles" because the word isn't in its English dictionary. This regex
// matches any "jarvis-like" token and, when a wake verb like "hey" is
// present, also accepts it alone as a wake phrase.
const WAKE_REGEX = /\b(?:hey|hi|ok|okay|yo|hello)\s+(?:jarvis|jervis|javis|jarvice|jarvice|jarvus|jarvice|harvis|charvis|jarvy|jarbis|jarvi|jar|starvis|chuckles|charles|jerry|jervous|jarvix)\b|\bjarvis\b/i

function getSpeechRecognitionCtor() {
  if (typeof window === 'undefined') return null
  return window.SpeechRecognition || window.webkitSpeechRecognition || null
}

export default function useWakeWord({
  onWake,
  enabled = true,
  lang = 'en-US',
  verbose = true,
} = {}) {
  const [isListening, setIsListening] = useState(false)
  const [isSupported, setIsSupported] = useState(true)
  const [error, setError] = useState(null)
  const [lastTranscript, setLastTranscript] = useState('')

  const recognitionRef = useRef(null)
  const enabledRef = useRef(enabled)
  const onWakeRef = useRef(onWake)
  const restartTimerRef = useRef(null)
  const suppressAutoRestartRef = useRef(false)
  const pendingWakeRef = useRef(null)
  const startedAtRef = useRef(0)

  useEffect(() => {
    enabledRef.current = enabled
  }, [enabled])
  useEffect(() => {
    onWakeRef.current = onWake
  }, [onWake])

  const log = useCallback(
    (...args) => {
      if (verbose) {
        // eslint-disable-next-line no-console
        console.log('[wakeword]', ...args)
      }
    },
    [verbose]
  )

  const stop = useCallback(() => {
    suppressAutoRestartRef.current = true
    if (restartTimerRef.current) {
      clearTimeout(restartTimerRef.current)
      restartTimerRef.current = null
    }
    const rec = recognitionRef.current
    if (rec) {
      try {
        rec.onstart = null
        rec.onend = null
        rec.onresult = null
        rec.onerror = null
        rec.onaudiostart = null
        rec.onaudioend = null
        rec.onspeechstart = null
        rec.onspeechend = null
        rec.stop()
      } catch {
        // ignore — already stopped
      }
      recognitionRef.current = null
    }
    setIsListening(false)
  }, [])

  const start = useCallback(() => {
    if (recognitionRef.current) {
      log('start() called but recognition already running, ignoring')
      return
    }
    const SR = getSpeechRecognitionCtor()
    if (!SR) {
      log('SpeechRecognition API not available (not Chrome/Edge?)')
      setIsSupported(false)
      return
    }

    suppressAutoRestartRef.current = false
    const rec = new SR()
    rec.continuous = true
    rec.interimResults = true
    rec.maxAlternatives = 1
    rec.lang = lang

    rec.onstart = () => {
      startedAtRef.current = Date.now()
      log('onstart — recognition service started')
      setIsListening(true)
      setError(null)
    }

    rec.onaudiostart = () => log('onaudiostart — mic capture started')
    rec.onaudioend = () => log('onaudioend — mic capture stopped')
    rec.onspeechstart = () => log('onspeechstart — speech detected')
    rec.onspeechend = () => log('onspeechend — speech stopped')

    rec.onresult = (event) => {
      // Concatenate ALL results (finals + interim) every update so we never
      // miss a wake phrase that straddled a result boundary.
      let txt = ''
      for (let i = 0; i < event.results.length; i++) {
        txt += event.results[i][0].transcript
      }
      const cleaned = txt.trim()
      setLastTranscript(cleaned)
      log('onresult transcript:', JSON.stringify(cleaned))

      if (WAKE_REGEX.test(cleaned)) {
        const match = cleaned.match(WAKE_REGEX)?.[0] || 'jarvis'
        log('WAKE MATCH:', JSON.stringify(match))
        pendingWakeRef.current = match
        suppressAutoRestartRef.current = true
        try {
          rec.stop()
        } catch {
          // already stopped
        }
      }
    }

    rec.onerror = (event) => {
      const code = event?.error || 'unknown'
      log('onerror:', code, event?.message || '')
      setError(code)
      if (code === 'not-allowed' || code === 'service-not-allowed') {
        // Mic permission denied — give up. User must grant.
        suppressAutoRestartRef.current = true
      } else if (code === 'network') {
        // Google speech API unreachable; backoff + retry.
        log('network error; will retry')
      }
      // Other errors (no-speech, audio-capture, aborted) → onend will fire
      // and we'll auto-restart from there.
    }

    rec.onend = () => {
      const ranMs = Date.now() - startedAtRef.current
      log(`onend after ${ranMs}ms`)
      recognitionRef.current = null
      setIsListening(false)

      // Fire pending wake callback AFTER mic is fully released.
      const pending = pendingWakeRef.current
      if (pending) {
        pendingWakeRef.current = null
        const cb = onWakeRef.current
        log(`firing onWake for "${pending}"`)
        setTimeout(() => {
          if (typeof cb === 'function') {
            try {
              cb(pending)
            } catch (err) {
              // eslint-disable-next-line no-console
              console.error('[wakeword] onWake threw', err)
            }
          }
        }, 100)
        return
      }

      if (enabledRef.current && !suppressAutoRestartRef.current) {
        log('auto-restarting in 400ms')
        restartTimerRef.current = setTimeout(() => {
          restartTimerRef.current = null
          start()
        }, 400)
      } else {
        log('not restarting (enabled=' + enabledRef.current + ', suppress=' + suppressAutoRestartRef.current + ')')
      }
    }

    try {
      log('calling rec.start()')
      rec.start()
      recognitionRef.current = rec
    } catch (err) {
      // Re-start races can throw "InvalidStateError: recognition already
      // started". React StrictMode double-invokes effects, so swallow that one.
      if (err?.message && /already started/i.test(err.message)) {
        log('ignoring "already started" race')
        recognitionRef.current = rec
      } else {
        log('rec.start() threw:', err?.message || err)
        setError(err?.message || String(err))
      }
    }
  }, [lang, log])

  useEffect(() => {
    log('effect: enabled=' + enabled)
    if (enabled) {
      start()
    } else {
      stop()
    }
    return () => {
      log('effect cleanup')
      stop()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled])

  return {
    isListening,
    isSupported,
    error,
    lastTranscript,
    start,
    stop,
  }
}
