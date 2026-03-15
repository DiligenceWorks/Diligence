import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { api } from '../api'

export default function Dashboard() {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => { loadStatus() }, [])

  async function loadStatus() {
    try {
      const data = await api.today()
      setStatus(data)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  async function handleSync(provider) {
    try {
      const fn = provider === 'strava' ? api.stravaSync : api.polarSync
      await fn()
      await loadStatus()
    } catch (err) { alert(`Sync failed: ${err.message}`) }
  }

  if (loading) return <div className="page"><div className="loading">Loading...</div></div>
  if (!status) return <div className="page"><div className="error-msg">Failed to load</div></div>

  const pct = status.daily_minimum > 0 ? Math.min(100, Math.round((status.points_earned / status.daily_minimum) * 100)) : 0
  const weekPct = status.weekly_target > 0 ? Math.min(100, Math.round((status.week_points / status.weekly_target) * 100)) : 0

  const categories = {
    workout: { label: 'Workout', icon: '💪', pts: 50 },
    food_log: { label: 'Food logged', icon: '🥗', pts: 30 },
    steps_target: { label: 'Steps target', icon: '👟', pts: 20 },
    screen_free: { label: 'Screen-free time', icon: '📖', pts: '20/hr' },
    daily_checkin: { label: 'Daily check-in', icon: '✅', pts: 10 },
  }
  const doneCats = new Set(status.activities_today.map(a => a.category))

  return (
    <div className="page">
      {/* Program progress */}
      {status.program_name && (
        <div className="card" style={{ textAlign: 'center', padding: '16px 20px', background: 'var(--blue-bg)', borderColor: 'rgba(59, 130, 246, 0.15)' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            {status.program_name}
          </div>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.1rem', margin: '4px 0', color: 'var(--blue)' }}>
            Day {status.program_day} of {status.program_total_days}
          </div>
          <div className="progress-bar" style={{ height: '6px' }}>
            <div className="progress-bar-fill" style={{
              width: `${Math.round((status.program_day / status.program_total_days) * 100)}%`,
              background: 'linear-gradient(90deg, #3b82f6, #60a5fa)'
            }} />
          </div>
        </div>
      )}

      {/* Gate banner */}
      <div className={`gate-banner ${status.gate_passed ? 'gate-earned' : 'gate-locked'}`}>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Today</div>
        <div className="gate-pts">
          <span style={{ color: status.gate_passed ? 'var(--success)' : 'var(--danger)' }}>
            {status.points_earned}
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: '1rem', fontFamily: 'var(--font-body)', fontWeight: 500 }}> / {status.daily_minimum} pts</span>
        </div>
        <div className="progress-bar" style={{ marginTop: '10px', height: '8px' }}>
          <div className="progress-bar-fill" style={{
            width: `${pct}%`,
            background: status.gate_passed
              ? 'linear-gradient(90deg, #22c55e, #4ade80)'
              : 'linear-gradient(90deg, #ff6b35, #ff8f5e)',
          }} />
        </div>
        <div style={{ marginTop: '10px', fontSize: '0.88rem', fontWeight: 700 }}>
          {status.gate_passed
            ? <span style={{ color: 'var(--success)' }}>✨ Rewards Unlocked!</span>
            : <span style={{ color: 'var(--text-secondary)' }}>🔒 {status.points_remaining} more pts to unlock</span>
          }
        </div>
      </div>

      {/* Week progress */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.03em' }}>This Week</span>
          <Link to="/week" style={{ fontSize: '0.82rem', fontWeight: 600 }}>View Details →</Link>
        </div>
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.1rem', marginBottom: '8px' }}>
          {status.week_points} <span style={{ fontFamily: 'var(--font-body)', fontWeight: 500, fontSize: '0.85rem', color: 'var(--text-muted)' }}>/ {status.weekly_target} pts</span>
        </div>
        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${weekPct}%`, background: 'linear-gradient(90deg, #8b5cf6, #a78bfa)' }} />
        </div>
      </div>

      {/* Activity checklist */}
      <div className="card">
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, marginBottom: '8px', fontSize: '1rem' }}>Today's Activities</div>
        {Object.entries(categories).map(([cat, info]) => (
          <div className="checklist-item" key={cat}>
            <span className="checklist-check">{doneCats.has(cat) ? '✅' : '⬜'}</span>
            <span style={{ fontWeight: 500 }}>{info.icon} {info.label}</span>
            <span className="checklist-points">+{info.pts}</span>
          </div>
        ))}
      </div>

      {/* Rewards (if gate passed) */}
      {status.gate_passed && status.rewards_available.length > 0 && (
        <div className="card" style={{ background: 'var(--success-bg)', borderColor: 'rgba(34, 197, 94, 0.15)' }}>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, marginBottom: '10px', fontSize: '1rem', color: 'var(--success)' }}>🎮 Rewards Available</div>
          {status.rewards_available.map(r => (
            <div className="reward-card" key={r.id}>
              <div>
                <div style={{ fontWeight: 600 }}>{r.name}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 500 }}>{r.point_cost} pts</div>
              </div>
              <button className="btn-success btn-sm" onClick={async () => {
                try { await api.redeemReward(r.id); await loadStatus() }
                catch (err) { alert(err.message) }
              }}>Redeem</button>
            </div>
          ))}
        </div>
      )}

      {/* Quick actions */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '8px' }}>
        <button className="btn-primary btn-full" onClick={() => navigate('/log')}>+ Log Activity</button>
        <button className="btn-outline btn-full" onClick={() => navigate('/food')}>🍽️ Log Food</button>
        <button className="btn-outline btn-full btn-sm" onClick={() => handleSync('strava')} style={{ fontSize: '0.78rem' }}>🔄 Sync Strava</button>
        <button className="btn-outline btn-full btn-sm" onClick={() => handleSync('polar')} style={{ fontSize: '0.78rem' }}>🔄 Sync Polar</button>
      </div>
    </div>
  )
}
