import { useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../AuthProvider'

export default function LoginPage() {
  const { session, loading, signIn, signUp } = useAuth()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [info, setInfo] = useState(null)

  if (loading) return null
  if (session) {
    const to = location.state?.from?.pathname || '/'
    return <Navigate to={to} replace />
  }

  const run = async (fn, label) => {
    setError(null)
    setInfo(null)
    setBusy(true)
    try {
      await fn(email.trim(), password)
      if (label === 'sign-up') {
        setInfo(
          'Account created. If email confirmation is enabled in Supabase, check your inbox, then sign in.'
        )
      }
    } catch (e) {
      setError(e?.message || 'Something went wrong.')
    } finally {
      setBusy(false)
    }
  }

  const handleSignIn = (e) => {
    e?.preventDefault()
    if (!email || !password) {
      setError('Email and password are required.')
      return
    }
    run(signIn, 'sign-in')
  }

  const handleSignUp = () => {
    if (!email || !password) {
      setError('Email and password are required.')
      return
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }
    run(signUp, 'sign-up')
  }

  return (
    <div
      style={{
        width: '100vw',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background:
          'radial-gradient(circle at 30% 20%, rgba(0, 212, 255, 0.08) 0%, #020d1a 55%)',
        fontFamily:
          'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
        color: '#e6f6ff',
      }}
    >
      <form
        onSubmit={handleSignIn}
        style={{
          width: 380,
          padding: 36,
          borderRadius: 16,
          background: 'rgba(2, 13, 26, 0.85)',
          border: '1px solid rgba(0, 212, 255, 0.35)',
          boxShadow: '0 0 48px rgba(0, 212, 255, 0.18)',
          display: 'flex',
          flexDirection: 'column',
          gap: 18,
        }}
      >
        <div>
          <div
            style={{
              fontFamily: 'monospace',
              fontSize: 28,
              letterSpacing: 8,
              color: '#00d4ff',
              textShadow: '0 0 12px rgba(0, 212, 255, 0.5)',
            }}
          >
            J.A.R.V.I.S
          </div>
          <div
            style={{
              fontFamily: 'monospace',
              fontSize: 11,
              letterSpacing: 3,
              color: 'rgba(0, 212, 255, 0.55)',
              marginTop: 2,
            }}
          >
            ADMIN AUTHENTICATION
          </div>
        </div>

        <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <span style={{ fontSize: 12, color: 'rgba(230, 246, 255, 0.6)' }}>
            EMAIL
          </span>
          <input
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={inputStyle}
            placeholder="you@qut.edu.au"
          />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <span style={{ fontSize: 12, color: 'rgba(230, 246, 255, 0.6)' }}>
            PASSWORD
          </span>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={inputStyle}
            placeholder="••••••••"
          />
        </label>

        {error && <div style={errorStyle}>{error}</div>}
        {info && <div style={infoStyle}>{info}</div>}

        <div style={{ display: 'flex', gap: 10 }}>
          <button
            type="submit"
            disabled={busy}
            style={{ ...primaryBtn, flex: 1 }}
          >
            {busy ? 'WORKING…' : 'SIGN IN'}
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={handleSignUp}
            style={{ ...secondaryBtn, flex: 1 }}
          >
            CREATE ACCOUNT
          </button>
        </div>

        <div
          style={{
            fontSize: 11,
            color: 'rgba(230, 246, 255, 0.35)',
            fontFamily: 'monospace',
            marginTop: 4,
          }}
        >
          Using Supabase Auth @ eredinmxmdlgeqfmgtsm.supabase.co
        </div>
      </form>
    </div>
  )
}

const inputStyle = {
  padding: '11px 14px',
  borderRadius: 8,
  border: '1px solid rgba(0, 212, 255, 0.3)',
  background: 'rgba(0, 20, 40, 0.6)',
  color: '#e6f6ff',
  fontSize: 14,
  outline: 'none',
}

const primaryBtn = {
  padding: '11px 14px',
  borderRadius: 8,
  border: '1px solid rgba(0, 212, 255, 0.7)',
  background: 'rgba(0, 212, 255, 0.2)',
  color: '#00d4ff',
  fontFamily: 'monospace',
  fontSize: 13,
  letterSpacing: 2,
  cursor: 'pointer',
  fontWeight: 600,
}

const secondaryBtn = {
  padding: '11px 14px',
  borderRadius: 8,
  border: '1px solid rgba(230, 246, 255, 0.2)',
  background: 'transparent',
  color: 'rgba(230, 246, 255, 0.75)',
  fontFamily: 'monospace',
  fontSize: 13,
  letterSpacing: 2,
  cursor: 'pointer',
}

const errorStyle = {
  padding: '10px 12px',
  borderRadius: 8,
  background: 'rgba(255, 80, 80, 0.1)',
  border: '1px solid rgba(255, 80, 80, 0.4)',
  color: 'rgba(255, 170, 170, 0.95)',
  fontSize: 12,
  fontFamily: 'monospace',
}

const infoStyle = {
  padding: '10px 12px',
  borderRadius: 8,
  background: 'rgba(0, 212, 255, 0.08)',
  border: '1px solid rgba(0, 212, 255, 0.35)',
  color: 'rgba(170, 230, 255, 0.95)',
  fontSize: 12,
  fontFamily: 'monospace',
}
