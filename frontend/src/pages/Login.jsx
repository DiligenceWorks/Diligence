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
      const data = mode === 'login'
        ? await api.login(username, password)
        : await api.register(username, password, displayName || username)
      setToken(data.access_token)
      const status = await api.onboardingStatus()
      navigate(status.phase1_completed ? '/' : '/onboarding')
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  return (
    <div style={{
      minHeight: '100dvh',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      padding: '24px',
      background: 'linear-gradient(170deg, var(--accent-light) 0%, var(--accent) 30%, var(--accent-dark) 60%, var(--text) 100%)',
    }}>
      <div style={{ width: '100%', maxWidth: '380px' }}>
        {/* Brand */}
        <div style={{ textAlign: 'center', marginBottom: '32px', color: '#fff' }}>
          <div style={{ fontSize: '3.2rem', marginBottom: '8px', filter: 'drop-shadow(0 4px 12px rgba(0,0,0,0.2))' }}>🔥</div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2.2rem', fontWeight: 900, letterSpacing: '-0.03em' }}>
            Fitness Rewards
          </h1>
          <p style={{ opacity: 0.8, marginTop: '4px', fontSize: '0.95rem', fontWeight: 500 }}>
            Earn your rewards. Every single day.
          </p>
        </div>

        {/* Form card */}
        <div style={{
          background: 'var(--card)', borderRadius: 'var(--r-lg)', padding: '28px',
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
        }}>
          {/* Toggle */}
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px',
            background: 'rgba(0,0,0,0.04)', borderRadius: 'var(--r)', padding: '4px', marginBottom: '24px',
          }}>
            {['login', 'register'].map(m => (
              <button key={m} type="button"
                onClick={() => setMode(m)}
                style={{
                  borderRadius: 'var(--r-sm)', padding: '10px',
                  fontWeight: 700, fontSize: '0.85rem',
                  background: mode === m ? 'var(--accent)' : 'transparent',
                  color: mode === m ? '#fff' : 'var(--text-2)',
                  boxShadow: mode === m ? 'var(--shadow-accent)' : 'none',
                }}>
                {m === 'login' ? 'Sign In' : 'Sign Up'}
              </button>
            ))}
          </div>

          {error && <div className="error-msg">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Username</label>
              <input value={username} onChange={e => setUsername(e.target.value)} required autoComplete="username" />
            </div>
            <div className="form-group">
              <label className="form-label">Password</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} required autoComplete="current-password" />
            </div>
            {mode === 'register' && (
              <div className="form-group">
                <label className="form-label">Display Name</label>
                <input value={displayName} onChange={e => setDisplayName(e.target.value)} placeholder="What should we call you?" />
              </div>
            )}
            <button type="submit" className="btn-primary btn-full" disabled={loading}
              style={{ padding: '14px', fontSize: '0.95rem', marginTop: '8px', borderRadius: 'var(--r)' }}>
              {loading ? '...' : mode === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
