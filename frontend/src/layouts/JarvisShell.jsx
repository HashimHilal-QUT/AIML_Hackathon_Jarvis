import { Link } from 'react-router-dom'

/**
 * No-op wrapper for the full-bleed Jarvis canvas route. Adds a floating
 * "Back to admin" pill in the top-left so you can navigate away without
 * touching JarvisCanvas.jsx itself.
 */
export default function JarvisShell({ children }) {
  return (
    <>
      {children}
      <Link
        to="/"
        style={{
          position: 'fixed',
          top: 16,
          left: 16,
          zIndex: 1000,
          padding: '8px 14px',
          borderRadius: 999,
          background: 'rgba(2, 13, 26, 0.85)',
          border: '1px solid rgba(0, 212, 255, 0.5)',
          color: '#00d4ff',
          fontFamily: 'monospace',
          fontSize: 12,
          letterSpacing: 2,
          textDecoration: 'none',
          backdropFilter: 'blur(6px)',
          boxShadow: '0 0 16px rgba(0, 212, 255, 0.25)',
        }}
      >
        ← ADMIN
      </Link>
    </>
  )
}
