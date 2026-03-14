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

      // Check onboarding status
      const status = await api.onboardingStatus()
      if (!status.phase1_completed) {
        navigate('/onboarding')
      } else {
        navigate('/')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page" style={{ paddingTop: '80px' }}>
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <div style={{ fontSize: '3rem', marginBottom: '8px' }}>🏆</div>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Fitness Rewards</h1>
        <p style={{ color: 'var(--text-muted)', marginTop: '8px' }}>Earn your rewards. Every day.</p>
      </div>

      <div className="card">
        <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
          <button
            className={mode === 'login' ? 'btn-primary btn-full' : 'btn-outline btn-full'}
            onClick={() => setMode('login')}
            type="button"
          >Sign In</button>
          <button
            className={mode === 'register' ? 'btn-primary btn-full' : 'btn-outline btn-full'}
            onClick={() => setMode('register')}
            type="button"
          >Sign Up</button>
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
          <button type="submit" className="btn-primary btn-full" disabled={loading}>
            {loading ? '...' : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  )
}
