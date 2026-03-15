import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, setToken } from '../api'

export default function Login() {
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      let data
      if (mode === 'login') {
        data = await api.login(username, password)
      } else {
        data = await api.register(username, password, displayName || username)
      }
      setToken(data.access_token)
      const status = await api.onboardingStatus()
      navigate(status.phase1_completed ? '/' : '/onboarding')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px', background: 'linear-gradient(160deg, #fff7f0 0%, #faf8f5 40%, #f0f4ff 100%)' }}>
      <div style={{ width: '100%', maxWidth: '400px' }}>

        {/* Logo & branding */}
        <div style={{ textAlign: 'center', marginBottom: '36px' }}>
          <div style={{
            width: '72px', height: '72px', borderRadius: '20px', margin: '0 auto 16px',
            background: 'linear-gradient(135deg, #ff6b35 0%, #ff8f5e 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '2rem', boxShadow: '0 8px 24px rgba(255, 107, 53, 0.3)',
          }}>🏆</div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.03em', color: 'var(--text)' }}>
            Fitness Rewards
          </h1>
          <p style={{ color: 'var(--text-muted)', marginTop: '6px', fontSize: '0.95rem' }}>
            Earn your rewards. Every day.
          </p>
        </div>

        {/* Card */}
        <div className="card" style={{ padding: '28px', boxShadow: 'var(--shadow-lg)' }}>
          {/* Tab toggle */}
          <div style={{
            display: 'flex', gap: '4px', marginBottom: '24px', padding: '4px',
            background: 'var(--bg)', borderRadius: 'var(--radius-full)',
          }}>
            <button
              className={mode === 'login' ? 'btn-primary btn-full' : 'btn-ghost btn-full'}
              onClick={() => setMode('login')} type="button"
              style={{ borderRadius: 'var(--radius-full)' }}
            >Sign In</button>
            <button
              className={mode === 'register' ? 'btn-primary btn-full' : 'btn-ghost btn-full'}
              onClick={() => setMode('register')} type="button"
              style={{ borderRadius: 'var(--radius-full)' }}
            >Sign Up</button>
          </div>

          {error && <div className="error-msg">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Username</label>
              <input value={username} onChange={e => setUsername(e.target.value)} required autoComplete="username" placeholder="your username" />
            </div>
            <div className="form-group">
              <label className="form-label">Password</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} required autoComplete="current-password" placeholder="your password" />
            </div>
            {mode === 'register' && (
              <div className="form-group">
                <label className="form-label">Display Name</label>
                <input value={displayName} onChange={e => setDisplayName(e.target.value)} placeholder="What should we call you?" />
              </div>
            )}
            <button type="submit" className="btn-primary btn-full" disabled={loading} style={{ padding: '14px', fontSize: '1rem', marginTop: '4px' }}>
              {loading ? 'Working...' : mode === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
