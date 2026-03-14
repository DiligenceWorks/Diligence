import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, clearToken } from '../api'

export default function Settings() {
  const [user, setUser] = useState(null)
  const [rules, setRules] = useState([])
  const [targets, setTargets] = useState(null)
  const [integrations, setIntegrations] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => { load() }, [])

  async function load() {
    try {
      const [u, r, t, intg] = await Promise.all([
        api.me(), api.getRules(), api.getTargets(), api.integrationStatus(),
      ])
      setUser(u); setRules(r); setTargets(t); setIntegrations(intg)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  async function updateRule(id, points) {
    try {
      await api.updateRule(id, { points: parseInt(points) })
    } catch (err) { alert(err.message) }
  }

  async function updateTargets(field, value) {
    const update = { [field]: parseInt(value) }
    try {
      await api.updateTargets(update)
      setTargets({ ...targets, ...update })
    } catch (err) { alert(err.message) }
  }

  async function connectProvider(provider) {
    try {
      const fn = provider === 'strava' ? api.stravaAuth : api.polarAuth
      const data = await fn()
      window.location.href = data.auth_url
    } catch (err) { alert(err.message) }
  }

  async function disconnectProvider(provider) {
    if (!confirm(`Disconnect ${provider}?`)) return
    try {
      await api.disconnect(provider)
      await load()
    } catch (err) { alert(err.message) }
  }

  function handleLogout() {
    clearToken()
    navigate('/login')
  }

  if (loading) return <div className="page"><div className="loading">Loading...</div></div>

  return (
    <div className="page">
      <h1 className="page-title">⚙️ Settings</h1>

      {/* User */}
      {user && (
        <div className="card">
          <div style={{ fontWeight: 700, marginBottom: '4px' }}>{user.display_name}</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>@{user.username}</div>
        </div>
      )}

      {/* Point Rules */}
      <div className="card">
        <div style={{ fontWeight: 700, marginBottom: '12px' }}>Point Rules</div>
        {rules.map(r => (
          <div key={r.id} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
            <div style={{ flex: 1, fontSize: '0.9rem' }}>{r.description}</div>
            <input
              type="number"
              style={{ width: '70px', textAlign: 'center' }}
              defaultValue={r.points}
              onBlur={e => updateRule(r.id, e.target.value)}
            />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>pts</span>
          </div>
        ))}
      </div>

      {/* Daily Targets */}
      {targets && (
        <div className="card">
          <div style={{ fontWeight: 700, marginBottom: '12px' }}>Daily Targets</div>
          <div className="form-group">
            <label className="form-label">Daily minimum (pts to unlock rewards)</label>
            <input type="number" defaultValue={targets.daily_minimum_pts} onBlur={e => updateTargets('daily_minimum_pts', e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Weekly target</label>
            <input type="number" defaultValue={targets.weekly_target_pts} onBlur={e => updateTargets('weekly_target_pts', e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Weekly bonus (for hitting target)</label>
            <input type="number" defaultValue={targets.weekly_bonus_pts} onBlur={e => updateTargets('weekly_bonus_pts', e.target.value)} />
          </div>
        </div>
      )}

      {/* Integrations */}
      <div className="card">
        <div style={{ fontWeight: 700, marginBottom: '12px' }}>Integrations</div>
        {['strava', 'polar'].map(provider => {
          const info = integrations?.[provider] || { connected: false }
          return (
            <div key={provider} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
              <div>
                <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{provider}</div>
                <div style={{ fontSize: '0.8rem', color: info.connected ? 'var(--success)' : 'var(--text-muted)' }}>
                  {info.connected ? 'Connected' : 'Not connected'}
                </div>
              </div>
              {info.connected ? (
                <button className="btn-outline btn-sm" onClick={() => disconnectProvider(provider)}>Disconnect</button>
              ) : (
                <button className="btn-primary btn-sm" onClick={() => connectProvider(provider)}>Connect</button>
              )}
            </div>
          )
        })}
      </div>

      {/* Logout */}
      <button className="btn-danger btn-full" style={{ marginTop: '16px' }} onClick={handleLogout}>Sign Out</button>
    </div>
  )
}
