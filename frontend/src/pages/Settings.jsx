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
      const [u, r, t, intg] = await Promise.all([api.me(), api.getRules(), api.getTargets(), api.integrationStatus()])
      setUser(u); setRules(r); setTargets(t); setIntegrations(intg)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }
  async function updateRule(id, points) {
    try { await api.updateRule(id, { points: parseInt(points) }) } catch (err) { alert(err.message) }
  }
  async function updateTargets(field, value) {
    const update = { [field]: parseInt(value) }
    try { await api.updateTargets(update); setTargets({ ...targets, ...update }) } catch (err) { alert(err.message) }
  }
  async function connectProvider(provider) {
    try {
      const data = await (provider === 'strava' ? api.stravaAuth : api.polarAuth)()
      window.location.href = data.auth_url
    } catch (err) { alert(err.message) }
  }
  async function disconnectProvider(provider) {
    if (!confirm(`Disconnect ${provider}?`)) return
    try { await api.disconnect(provider); await load() } catch (err) { alert(err.message) }
  }

  if (loading) return <div className="page"><div className="loading">Loading...</div></div>

  return (
    <div className="page">
      <h1 className="page-title">Settings</h1>

      {/* User */}
      {user && (
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '48px', height: '48px', borderRadius: '14px',
            background: 'linear-gradient(135deg, #FF5722, #FF8A65)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '1.2rem',
          }}>
            {user.display_name.charAt(0).toUpperCase()}
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1rem' }}>{user.display_name}</div>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-3)', fontWeight: 500 }}>@{user.username}</div>
          </div>
        </div>
      )}

      {/* Point Rules */}
      <div className="card">
        <div className="section-label">Point Rules</div>
        {rules.map(r => (
          <div key={r.id} style={{
            display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 0',
            borderBottom: '1px solid var(--divider)',
          }}>
            <div style={{ flex: 1, fontSize: '0.88rem', fontWeight: 600 }}>{r.description}</div>
            <input type="number" style={{ width: '64px', textAlign: 'center', padding: '8px', fontWeight: 700 }}
              defaultValue={r.points} onBlur={e => updateRule(r.id, e.target.value)} />
            <span style={{ fontSize: '0.78rem', color: 'var(--text-3)', fontWeight: 600 }}>pts</span>
          </div>
        ))}
      </div>

      {/* Targets */}
      {targets && (
        <div className="card">
          <div className="section-label">Daily Targets</div>
          <div className="form-group">
            <label className="form-label">Daily minimum (unlock rewards)</label>
            <input type="number" defaultValue={targets.daily_minimum_pts} onBlur={e => updateTargets('daily_minimum_pts', e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Weekly target</label>
            <input type="number" defaultValue={targets.weekly_target_pts} onBlur={e => updateTargets('weekly_target_pts', e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Weekly bonus</label>
            <input type="number" defaultValue={targets.weekly_bonus_pts} onBlur={e => updateTargets('weekly_bonus_pts', e.target.value)} />
          </div>
        </div>
      )}

      {/* Integrations */}
      <div className="card">
        <div className="section-label">Integrations</div>
        {['strava', 'polar'].map(provider => {
          const info = integrations?.[provider] || { connected: false }
          return (
            <div key={provider} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '12px 0', borderBottom: '1px solid var(--divider)',
            }}>
              <div>
                <div style={{ fontWeight: 700, textTransform: 'capitalize', fontSize: '0.95rem' }}>{provider}</div>
                <div style={{ fontSize: '0.78rem', color: info.connected ? 'var(--green-dark)' : 'var(--text-3)', fontWeight: 600 }}>
                  {info.connected ? '● Connected' : 'Not connected'}
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

      <button className="btn-danger btn-full" style={{ marginTop: '10px' }} onClick={() => { clearToken(); navigate('/login') }}>
        Sign Out
      </button>
    </div>
  )
}
