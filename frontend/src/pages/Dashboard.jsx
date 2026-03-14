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
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  async function handleSync(provider) {
    try {
      const fn = provider === 'strava' ? api.stravaSync : api.polarSync
      await fn()
      await loadStatus()
    } catch (err) {
      alert(`Sync failed: ${err.message}`)
    }
  }

  if (loading) return <div className="page"><div className="loading">Loading...</div></div>
  if (!status) return <div className="page"><div className="error-msg">Failed to load</div></div>

  const pct = status.daily_minimum > 0 ? Math.min(100, Math.round((status.points_earned / status.daily_minimum) * 100)) : 0
  const weekPct = status.weekly_target > 0 ? Math.min(100, Math.round((status.week_points / status.weekly_target) * 100)) : 0

  // Build checklist from activities
  const categories = {
    workout: { label: 'Workout', icon: '💪', pts: 50 },
    food_log: { label: 'Food logged', icon: '🍽️', pts: 30 },
    steps_target: { label: 'Steps target', icon: '👟', pts: 20 },
    screen_free: { label: 'Screen-free time', icon: '📚', pts: '20/hr' },
    daily_checkin: { label: 'Daily check-in', icon: '✅', pts: 10 },
  }
  const doneCats = new Set(status.activities_today.map(a => a.category))

  return (
    <div className="page">
      {/* Program progress */}
      {status.program_name && (
        <div className="card" style={{ textAlign: 'center', padding: '14px 20px' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            {status.program_name}
          </div>
          <div style={{ fontWeight: 700, margin: '4px 0' }}>
            Day {status.program_day} of {status.program_total_days}
          </div>
          <div className="progress-bar">
            <div className="progress-bar-fill" style={{
              width: `${Math.round((status.program_day / status.program_total_days) * 100)}%`,
              background: 'var(--accent)'
            }} />
          </div>
        </div>
      )}

      {/* Gate banner */}
      <div className={`gate-banner ${status.gate_passed ? 'gate-earned' : 'gate-locked'}`}>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>TODAY</div>
        <div className="gate-pts">
          <span className={status.gate_passed ? 'status-earned' : 'status-locked'}>
            {status.points_earned}
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: '1.2rem' }}> / {status.daily_minimum} pts</span>
        </div>
        <div className="progress-bar" style={{ marginTop: '8px' }}>
          <div className="progress-bar-fill" style={{
            width: `${pct}%`,
            background: status.gate_passed ? 'var(--success)' : 'var(--danger)'
          }} />
        </div>
        <div style={{ marginTop: '8px', fontSize: '0.9rem', fontWeight: 600 }}>
          {status.gate_passed ? '✅ REWARDS UNLOCKED' : `🔒 Earn ${status.points_remaining} more pts to unlock`}
        </div>
      </div>

      {/* Week progress */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>This Week</span>
          <Link to="/week" style={{ fontSize: '0.85rem' }}>Details →</Link>
        </div>
        <div style={{ fontWeight: 700, marginBottom: '6px' }}>
          {status.week_points} / {status.weekly_target} pts
        </div>
        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${weekPct}%`, background: 'var(--accent)' }} />
        </div>
      </div>

      {/* Activity checklist */}
      <div className="card">
        <div style={{ fontWeight: 700, marginBottom: '10px', fontSize: '0.95rem' }}>Today's Activities</div>
        {Object.entries(categories).map(([cat, info]) => (
          <div className="checklist-item" key={cat}>
            <span className="checklist-check">{doneCats.has(cat) ? '✅' : '⬜'}</span>
            <span>{info.icon} {info.label}</span>
            <span className="checklist-points">+{info.pts}</span>
          </div>
        ))}
      </div>

      {/* Rewards (if gate passed) */}
      {status.gate_passed && status.rewards_available.length > 0 && (
        <div className="card">
          <div style={{ fontWeight: 700, marginBottom: '10px', fontSize: '0.95rem' }}>🎮 Rewards Available</div>
          {status.rewards_available.map(r => (
            <div className="reward-card" key={r.id}>
              <div>
                <div style={{ fontWeight: 600 }}>{r.name}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{r.point_cost} pts</div>
              </div>
              <button className="btn-success btn-sm" onClick={async () => {
                try {
                  await api.redeemReward(r.id)
                  await loadStatus()
                } catch (err) { alert(err.message) }
              }}>Redeem</button>
            </div>
          ))}
        </div>
      )}

      {/* Quick actions */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '8px' }}>
        <button className="btn-primary btn-full" onClick={() => navigate('/log')}>+ Log Activity</button>
        <button className="btn-outline btn-full" onClick={() => navigate('/food')}>📷 Log Food</button>
        <button className="btn-outline btn-full btn-sm" onClick={() => handleSync('strava')}>🔄 Sync Strava</button>
        <button className="btn-outline btn-full btn-sm" onClick={() => handleSync('polar')}>🔄 Sync Polar</button>
      </div>
    </div>
  )
}
