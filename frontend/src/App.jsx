import { Routes, Route, Navigate } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import Dashboard from './pages/Dashboard'
import BotSimulator from './pages/BotSimulator'
import TelephonySimulator from './pages/TelephonySimulator'
import RealTimeCall from './pages/RealTimeCall'
import './App.css'

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/admin" element={<Dashboard />} />
      {/* Redirect legacy /dashboard path to /admin */}
      <Route path="/dashboard" element={<Navigate to="/admin" replace />} />
      <Route path="/bot" element={<BotSimulator />} />
      <Route path="/telephony" element={<TelephonySimulator />} />
      <Route path="/call" element={<RealTimeCall />} />
      {/* Catch-all: redirect unknown routes to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
