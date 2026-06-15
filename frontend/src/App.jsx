import { Routes, Route, Navigate, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { hasToken, clearToken, api } from './api'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import LogActivity from './pages/LogActivity'
import LogFood from './pages/LogFood'
import Nutrition from './pages/Nutrition'
import Rewards from './pages/Rewards'
import Settings from './pages/Settings'
import Onboarding from './pages/Onboarding'
import WeekView from './pages/WeekView'
import Welcome from './pages/Welcome'
import SettingsIntegrations from './pages/SettingsIntegrations'
import MealPlan from './pages/MealPlan' 
import ProgramSearch from './pages/ProgramSearch'
import ProgramDetail from './pages/ProgramDetail'
import CatalogDetail from './pages/CatalogDetail'
import Support from './pages/Support'
import SupportAdmin from './pages/SupportAdmin'

function ProtectedRoute({ children }) {
  if (!hasToken()) return <Navigate to="/login" />
  return children
}

function HelpButton() {
  const [unread, setUnread] = useState(0)
  const navigate = useNavigate()
  const location = useLocation()

  // Don't show on login/onboarding/support pages
  const hidden = ['/login', '/onboarding', '/support'].some(p => location.pathname.startsWith(p))
  if (hidden) return null

  useEffect(() => {
    if (!hasToken()) return
    api.getUnreadCount()
      .then(d => setUnread(d.unread || 0))
      .catch(() => {})
    // Poll every 60s for new replies
    const interval = setInterval(() => {
      api.getUnreadCount()
        .then(d => setUnread(d.unread || 0))
        .catch(() => {})
    }, 60000)
    return () => clearInterval(interval)
  }, [location.pathname])

  return (
    <button
      onClick={() => navigate('/support')}
      style={{
        position: 'fixed', top: '12px', right: '12px', zIndex: 90,
        width: '40px', height: '40px', borderRadius: '50%',
        background: 'var(--card)', boxShadow: 'var(--shadow-2)',
        border: '1px solid var(--divider)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '1.1rem', padding: 0, cursor: 'pointer',
      }}
    >
      ?
      {unread > 0 && (
        <span style={{
          position: 'absolute', top: '-4px', right: '-4px',
          background: 'var(--red)', color: '#fff', fontSize: '0.6rem', fontWeight: 800,
          width: '18px', height: '18px', borderRadius: '50%',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          border: '2px solid var(--bg)',
        }}>
          {unread}
        </span>
      )}
    </button>
  )
}

function NavBar() {
  return (
    <nav className="nav-bar">
      <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <span className="nav-icon">🏠</span> Home
      </NavLink>
      <NavLink to="/log" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <span className="nav-icon">💪</span> Log
      </NavLink>
      <NavLink to="/nutrition" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <span className="nav-icon">🥑</span> Keto
      </NavLink>
      <NavLink to="/programs" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <span className="nav-icon">📋</span> Programs
      </NavLink>
      <NavLink to="/settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <span className="nav-icon">⚙️</span> More
      </NavLink>
    </nav>
  )
}

export default function App() {
  return (
    <>
      {hasToken() && <HelpButton />}
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/onboarding" element={<ProtectedRoute><Onboarding /></ProtectedRoute>} />
        <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/log" element={<ProtectedRoute><LogActivity /></ProtectedRoute>} />
        <Route path="/food" element={<ProtectedRoute><LogFood /></ProtectedRoute>} />
        <Route path="/nutrition" element={<ProtectedRoute><Nutrition /></ProtectedRoute>} />
        <Route path="/programs" element={<ProtectedRoute><ProgramSearch /></ProtectedRoute>} />
        <Route path="/programs/:id" element={<ProtectedRoute><ProgramDetail /></ProtectedRoute>} />
        <Route path="/catalog/:id" element={<ProtectedRoute><CatalogDetail /></ProtectedRoute>} />
        <Route path="/rewards" element={<ProtectedRoute><Rewards /></ProtectedRoute>} />
        <Route path="/week" element={<ProtectedRoute><WeekView /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
        <Route path="/support" element={<ProtectedRoute><Support /></ProtectedRoute>} />
        <Route path="/support/admin" element={<ProtectedRoute><SupportAdmin /></ProtectedRoute>} />
        <Route path="/support/admin/:threadId" element={<ProtectedRoute><SupportAdmin /></ProtectedRoute>} />
      </Routes>
      {hasToken() && <NavBar />}
    </>
  )
}
