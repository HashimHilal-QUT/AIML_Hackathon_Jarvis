import { NavLink } from 'react-router-dom'

const TABS = [
  { to: '/meal-buddy', label: 'Hub', icon: '🍽️', end: true, accent: '#ff6b9d' },
  { to: '/meal-buddy/preferences', label: 'Preferences', icon: '🍜', accent: '#ff6b9d' },
  { to: '/meal-buddy/discover', label: 'Discover', icon: '🔥', accent: '#00d4ff' },
  { to: '/meal-buddy/availability', label: 'Availability', icon: '📆', accent: '#f5a623' },
  { to: '/meal-buddy/matches', label: 'Matches', icon: '🤝', accent: '#7fffa0' },
]

/**
 * Persistent sub-navigation for all /meal-buddy/* pages. Renders as a
 * sticky horizontal pill bar that mirrors the cyberpunk cyan/gold theme.
 * Each page simply imports this and drops it at the top — no prop drilling.
 */
export default function MealBuddyNav() {
  return (
    <nav
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        marginBottom: 20,
        marginLeft: -8,
        marginRight: -8,
        padding: '10px 8px',
        background: 'rgba(2, 13, 26, 0.88)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid rgba(255, 107, 157, 0.18)',
        display: 'flex',
        gap: 6,
        alignItems: 'center',
        overflowX: 'auto',
      }}
    >
      <div
        style={{
          fontFamily: 'monospace',
          fontSize: 10,
          letterSpacing: 2,
          color: 'rgba(255, 107, 157, 0.55)',
          paddingRight: 12,
          borderRight: '1px solid rgba(255, 107, 157, 0.2)',
          marginRight: 6,
          whiteSpace: 'nowrap',
        }}
      >
        MEAL &amp; FRIENDS //
      </div>
      {TABS.map((tab) => (
        <NavLink
          key={tab.to}
          to={tab.to}
          end={tab.end}
          style={({ isActive }) => ({
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '8px 14px',
            borderRadius: 999,
            border: isActive
              ? `1px solid ${tab.accent}`
              : '1px solid rgba(0, 212, 255, 0.18)',
            background: isActive
              ? `${tab.accent}22`
              : 'rgba(0, 20, 40, 0.4)',
            color: isActive ? tab.accent : 'rgba(230, 246, 255, 0.6)',
            fontFamily: 'monospace',
            fontSize: 11,
            letterSpacing: 1.5,
            textTransform: 'uppercase',
            textDecoration: 'none',
            fontWeight: isActive ? 600 : 500,
            boxShadow: isActive ? `0 0 14px ${tab.accent}33` : 'none',
            transition: 'all 120ms ease-out',
            whiteSpace: 'nowrap',
          })}
        >
          <span style={{ fontSize: 13 }}>{tab.icon}</span>
          {tab.label}
        </NavLink>
      ))}
    </nav>
  )
}
