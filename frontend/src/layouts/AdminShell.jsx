import { useEffect } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../AuthProvider'

const SIDEBAR_ITEMS = [
  { to: '/', label: 'Home', icon: '🏠', end: true },
  { to: '/jarvis', label: 'Jarvis', icon: '🎙️' },
  { to: '/event', label: 'Event', icon: '📅' },
  { to: '/subjects', label: 'Subjects', icon: '📚' },
  { to: '/meal-buddy', label: 'Meal & Friends', icon: '🍽️' },
]

export default function AdminShell() {
  const { user, signOut } = useAuth()

  // App.css sets `body { overflow: hidden }` so the Jarvis canvas can't scroll.
  // We need scroll on admin pages. Toggle it while this layout is mounted.
  useEffect(() => {
    const prev = document.body.style.overflow
    document.body.style.overflow = 'auto'
    document.body.classList.add('admin-shell-active')
    return () => {
      document.body.style.overflow = prev
      document.body.classList.remove('admin-shell-active')
    }
  }, [])

  return (
    <div
      style={{
        display: 'flex',
        minHeight: '100vh',
        width: '100vw',
        background: '#020d1a',
        color: '#e6f6ff',
        fontFamily:
          'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
      }}
    >
      <aside
        style={{
          width: 240,
          minHeight: '100vh',
          background:
            'linear-gradient(180deg, rgba(0, 20, 40, 0.95) 0%, rgba(0, 8, 20, 0.98) 100%)',
          borderRight: '1px solid rgba(0, 212, 255, 0.18)',
          padding: '28px 18px',
          display: 'flex',
          flexDirection: 'column',
          gap: 24,
          position: 'sticky',
          top: 0,
          height: '100vh',
          boxShadow: '4px 0 24px rgba(0, 0, 0, 0.6)',
        }}
      >
        <div>
          <div
            style={{
              fontSize: 22,
              fontWeight: 700,
              letterSpacing: 6,
              color: '#00d4ff',
              fontFamily: 'monospace',
              textShadow: '0 0 12px rgba(0, 212, 255, 0.5)',
            }}
          >
            J.A.R.V.I.S
          </div>
          <div
            style={{
              fontSize: 11,
              color: 'rgba(0, 212, 255, 0.55)',
              letterSpacing: 2,
              fontFamily: 'monospace',
              marginTop: 4,
            }}
          >
            ADMIN // v1.0
          </div>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {SIDEBAR_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '11px 14px',
                borderRadius: 8,
                color: isActive ? '#00d4ff' : 'rgba(230, 246, 255, 0.72)',
                background: isActive
                  ? 'rgba(0, 212, 255, 0.12)'
                  : 'transparent',
                border: isActive
                  ? '1px solid rgba(0, 212, 255, 0.4)'
                  : '1px solid transparent',
                textDecoration: 'none',
                fontSize: 14,
                fontWeight: isActive ? 600 : 500,
                transition: 'all 120ms ease-out',
                boxShadow: isActive
                  ? '0 0 18px rgba(0, 212, 255, 0.18) inset'
                  : 'none',
              })}
            >
              <span style={{ fontSize: 16 }}>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {user?.email && (
            <div
              style={{
                fontSize: 11,
                color: 'rgba(230, 246, 255, 0.5)',
                fontFamily: 'monospace',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {user.email}
            </div>
          )}
          <button
            type="button"
            onClick={signOut}
            style={{
              background: 'rgba(255, 80, 80, 0.08)',
              border: '1px solid rgba(255, 80, 80, 0.35)',
              color: 'rgba(255, 160, 160, 0.95)',
              padding: '8px 12px',
              borderRadius: 8,
              fontFamily: 'monospace',
              fontSize: 12,
              letterSpacing: 1,
              cursor: 'pointer',
            }}
          >
            SIGN OUT
          </button>
        </div>
      </aside>

      <main
        style={{
          flex: 1,
          minHeight: '100vh',
          padding: '32px 40px',
          overflow: 'auto',
        }}
      >
        <Outlet />
      </main>
    </div>
  )
}
