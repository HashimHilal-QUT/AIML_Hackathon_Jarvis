import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import WelcomeOnboarding from './pages/WelcomeOnboarding'
import DiningPreferences from './pages/DiningPreferences'
import Discover from './pages/Discover'
import MatchDetails from './pages/MatchDetails'
import SetAvailability from './pages/SetAvailability'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/welcome" replace />} />
        <Route path="/welcome" element={<WelcomeOnboarding />} />
        <Route path="/dining-preferences" element={<DiningPreferences />} />
        <Route path="/discover" element={<Discover />} />
        <Route path="/matches" element={<MatchDetails />} />
        <Route path="/availability" element={<SetAvailability />} />
        <Route path="*" element={<Navigate to="/welcome" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
