import { Link } from 'react-router-dom'
import { useAuth } from '../AuthProvider'

export default function HomePage() {
  const { user } = useAuth()
  return (
    <div style={{ maxWidth: 1100, margin: '0 auto' }}>
      <header style={{ marginBottom: 40 }}>
        <div
          style={{
            fontFamily: 'monospace',
            fontSize: 11,
            letterSpacing: 3,
            color: 'rgba(0, 212, 255, 0.6)',
            marginBottom: 4,
          }}
        >
          SYS.CORE // ADMIN CONSOLE
        </div>
        <h1
          style={{
            fontSize: 42,
            margin: 0,
            fontWeight: 700,
            letterSpacing: -0.5,
          }}
        >
          Welcome back{user?.email ? `, ${user.email.split('@')[0]}` : ''}.
        </h1>
        <p
          style={{
            color: 'rgba(230, 246, 255, 0.6)',
            fontSize: 15,
            marginTop: 8,
            maxWidth: 560,
          }}
        >
          Manage your JARVIS assistant. Connect your QUT calendars, talk to the
          voice interface, or review your upcoming schedule.
        </p>
      </header>

      <section
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: 20,
        }}
      >
        <Card
          to="/jarvis"
          accent="#00d4ff"
          emoji="🎙️"
          title="JARVIS VOICE"
          subtitle="Talk to Jarvis"
          body="Open the full-screen voice interface. Ask questions, get spoken answers, control your session."
        />
        <Card
          to="/event"
          accent="#ff9500"
          emoji="📅"
          title="EVENT CALENDAR"
          subtitle="Sync your schedule"
          body="Paste your QUT Timetable and Canvas links. Jarvis pulls every class and assignment and keeps them in one calendar."
        />
        <Card
          to="/subjects"
          accent="#7fffa0"
          emoji="📚"
          title="SUBJECTS"
          subtitle="Course helper"
          body="Add your subjects with syllabus, modules, assignment rubrics, and slides. Jarvis uses them as context to answer course questions."
        />
        <Card
          to="/meal-buddy"
          accent="#ff6b9d"
          emoji="🍽️"
          title="MEAL & FRIENDS"
          subtitle="Dining matchmaker"
          body="Set your cuisine, budget, and dietary flags. Pick restaurants, mark when you're free, and let Jarvis find a dining buddy."
        />
      </section>

      <section
        style={{
          marginTop: 48,
          padding: 20,
          borderRadius: 12,
          border: '1px dashed rgba(0, 212, 255, 0.25)',
          background: 'rgba(0, 20, 40, 0.4)',
          color: 'rgba(230, 246, 255, 0.6)',
          fontSize: 13,
          lineHeight: 1.6,
        }}
      >
        <strong style={{ color: '#00d4ff', fontFamily: 'monospace', letterSpacing: 2 }}>
          TIP //
        </strong>{' '}
        Go to <em>Event</em> first and add your QUT Timetable + Canvas URLs.
        After the first sync, Jarvis will answer schedule questions based on
        your real calendar.
      </section>
    </div>
  )
}

function Card({ to, accent, emoji, title, subtitle, body }) {
  return (
    <Link
      to={to}
      style={{
        display: 'block',
        textDecoration: 'none',
        color: 'inherit',
        padding: 24,
        borderRadius: 14,
        background:
          'linear-gradient(180deg, rgba(0, 30, 60, 0.7), rgba(0, 15, 30, 0.9))',
        border: `1px solid ${accent}33`,
        boxShadow: `0 0 32px ${accent}1f inset`,
        transition: 'transform 150ms ease-out, box-shadow 150ms ease-out',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)'
        e.currentTarget.style.boxShadow = `0 0 42px ${accent}33 inset, 0 12px 32px ${accent}22`
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = `0 0 32px ${accent}1f inset`
      }}
    >
      <div style={{ fontSize: 36, marginBottom: 12 }}>{emoji}</div>
      <div
        style={{
          fontFamily: 'monospace',
          fontSize: 11,
          letterSpacing: 3,
          color: accent,
        }}
      >
        {title}
      </div>
      <div style={{ fontSize: 22, fontWeight: 600, marginTop: 4 }}>
        {subtitle}
      </div>
      <div
        style={{
          fontSize: 13,
          color: 'rgba(230, 246, 255, 0.6)',
          marginTop: 10,
          lineHeight: 1.5,
        }}
      >
        {body}
      </div>
    </Link>
  )
}
