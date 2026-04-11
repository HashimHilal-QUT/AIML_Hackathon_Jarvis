import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './AuthProvider'
import AdminShell from './layouts/AdminShell'
import JarvisShell from './layouts/JarvisShell'
import AvailabilityPage from './pages/AvailabilityPage'
import DiningPreferencesPage from './pages/DiningPreferencesPage'
import DiscoverPage from './pages/DiscoverPage'
import EventPage from './pages/EventPage'
import HomePage from './pages/HomePage'
import JarvisPage from './pages/JarvisPage'
import LoginPage from './pages/LoginPage'
import MatchesPage from './pages/MatchesPage'
import MealBuddyHub from './pages/MealBuddyHub'
import SubjectDetailPage from './pages/SubjectDetailPage'
import SubjectsListPage from './pages/SubjectsListPage'

function ProtectedRoute() {
  const { session, loading } = useAuth()
  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '100vw',
          height: '100vh',
          background: '#020d1a',
          color: '#00d4ff',
          fontFamily: 'monospace',
        }}
      >
        Loading session…
      </div>
    )
  }
  if (!session) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            {/* /jarvis gets its own full-bleed shell (no sidebar) */}
            <Route
              path="/jarvis"
              element={
                <JarvisShell>
                  <JarvisPage />
                </JarvisShell>
              }
            />
            {/* / and /event share the sidebar admin shell */}
            <Route element={<AdminShell />}>
              <Route index element={<HomePage />} />
              <Route path="/event" element={<EventPage />} />
              <Route path="/subjects" element={<SubjectsListPage />} />
              <Route path="/subjects/:subjectId" element={<SubjectDetailPage />} />
              <Route path="/meal-buddy" element={<MealBuddyHub />} />
              <Route path="/meal-buddy/preferences" element={<DiningPreferencesPage />} />
              <Route path="/meal-buddy/discover" element={<DiscoverPage />} />
              <Route path="/meal-buddy/availability" element={<AvailabilityPage />} />
              <Route path="/meal-buddy/matches" element={<MatchesPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
