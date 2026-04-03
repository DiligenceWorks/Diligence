import { Routes, Route, Navigate, NavLink, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { hasToken, clearToken, api } from './api'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import LogActivity from './pages/LogActivity'
import LogFood from './pages/LogFood'
import Rewards from './pages/Rewards'
import Settings from './pages/Settings'
import Onboarding from './pages/Onboarding'
import WeekView from './pages/WeekView'
import ProgramSearch from './pages/ProgramSearch'
import ProgramDetail from './pages/ProgramDetail'

function ProtectedRoute({ children }) {
  if (!hasToken()) return <Navigate to="/login" />
  return children
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
      <NavLink to="/programs" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <span className="nav-icon">📋</span> Programs
      </NavLink>
      <NavLink to="/rewards" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <span className="nav-icon">🎮</span> Rewards
      </NavLink>
      <NavLink to="/settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <span className="nav-icon">⚙️</span> Settings
      </NavLink>
    </nav>
  )
}

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/onboarding" element={<ProtectedRoute><Onboarding /></ProtectedRoute>} />
        <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/log" element={<ProtectedRoute><LogActivity /></ProtectedRoute>} />
        <Route path="/food" element={<ProtectedRoute><LogFood /></ProtectedRoute>} />
        <Route path="/programs" element={<ProtectedRoute><ProgramSearch /></ProtectedRoute>} />
        <Route path="/programs/:id" element={<ProtectedRoute><ProgramDetail /></ProtectedRoute>} />
        <Route path="/rewards" element={<ProtectedRoute><Rewards /></ProtectedRoute>} />
        <Route path="/week" element={<ProtectedRoute><WeekView /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
      </Routes>
      {hasToken() && <NavBar />}
    </>
  )
}
