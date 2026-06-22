import { Routes, Route, Navigate } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import BotSimulator from './pages/BotSimulator'
import Dashboard from './pages/Dashboard'
import RealTimeCall from './pages/RealTimeCall'
import './App.css'

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/bot" element={<BotSimulator />} />
      <Route path="/call" element={<RealTimeCall />} />
      <Route path="/admin" element={<Dashboard />} />
      {/* Redirect legacy /dashboard path to /admin */}
      <Route path="/dashboard" element={<Navigate to="/admin" replace />} />
      {/* Redirect other pages to the single VoIP calling option */}
      <Route path="/telephony" element={<Navigate to="/call" replace />} />
      {/* Catch-all: redirect unknown routes to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
