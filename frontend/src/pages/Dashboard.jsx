import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { api } from '../api'

/* === Tooltip === */
function Tip({ text, children }) {
  const [show, setShow] = useState(false)
  return (
    <span style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}>
      {children}
      <span
        onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}
        onClick={(e) => { e.stopPropagation(); setShow(s => !s) }}
        style={{
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          width: '18px', height: '18px', borderRadius: '50%', marginLeft: '6px',
          background: 'rgba(0,0,0,0.06)', color: 'var(--text-3)', cursor: 'help',
          fontSize: '0.7rem', fontWeight: 800, flexShrink: 0,
        }}>?</span>
      {show && (
        <span style={{
          position: 'absolute', bottom: 'calc(100% + 8px)', left: '50%', transform: 'translateX(-50%)',
          background: 'var(--text)', color: '#fff', padding: '10px 14px', borderRadius: 'var(--r-sm)',
          fontSize: '0.78rem', lineHeight: 1.45, fontWeight: 500, width: '240px',
          boxShadow: 'var(--shadow-3)', zIndex: 50, pointerEvents: 'none',
        }}>{text}</span>
      )}
    </span>
  )
}

export default function Dashboard() {
  const [status, setStatus] = useState(null)
  const [integrations, setIntegrations] = useState(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(null)
  const navigate = useNavigate()

  useEffect(() => { loadAll() }, [])
  async function loadAll() {
    try {
      const [s, intg] = await Promise.all([api.today(), api.integrationStatus()])
      setStatus(s)
      setIntegrations(intg)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }
  async function handleSync(provider) {
    setSyncing(provider)
    try {
      const result = await (provider === 'strava' ? api.stravaSync : api.polarSync)()
      await loadAll()
      if (result.imported > 0) {
        alert(`Synced ${result.imported} activities from ${provider}!`)
      } else {
        alert(`No new activities found on ${provider}.`)
      }
    } catch (err) { alert(`Sync failed: ${err.message}`) }
    finally { setSyncing(null) }
  }
  async function handleConnect(provider) {
    try {
      const data = await (provider === 'strava' ? api.stravaAuth : api.polarAuth)()
      window.location.href = data.auth_url
    } catch (err) { alert(`Connect failed: ${err.message}`) }
  }

  if (loading) return <div className="page"><div className="loading">Loading...</div></div>
  if (!status) return <div className="page"><div className="error-msg">Failed to load</div></div>

  const pct = status.daily_minimum > 0 ? Math.min(100, Math.round((status.points_earned / status.daily_minimum) * 100)) : 0
  const weekPct = status.weekly_target > 0 ? Math.min(100, Math.round((status.week_points / status.weekly_target) * 100)) : 0
  const doneCats = new Set(status.activities_today.map(a => a.category))

  const stravaConnected = integrations?.strava?.connected
  const polarConnected = integrations?.polar?.connected

  const activities = [
    { key: 'workout', label: 'Workout', icon: '💪', pts: 50, color: '#FF5722', tip: 'Any exercise session — running, weights, yoga, etc. Logged manually or synced from Strava/Polar.' },
    { key: 'food_log', label: 'Food logged', icon: '🥗', pts: 30, color: '#4CAF50', tip: 'Log what you eat. Barcode scan or manual entry. Building food awareness is a key habit.' },
    { key: 'steps_target', label: 'Steps target', icon: '👟', pts: 20, color: '#2979FF', tip: 'Hit your daily step goal. Steps are the foundation of an active lifestyle.' },
    { key: 'screen_free', label: 'Screen-free', icon: '📖', pts: '20/hr', color: '#7C4DFF', tip: 'Time away from screens — reading, walking, hobbies. Points scale with hours logged.' },
    { key: 'daily_checkin', label: 'Check-in', icon: '✅', pts: 10, color: '#00BCD4', tip: 'Just show up and check in. The easiest points — consistency matters more than intensity.' },
  ]

  return (
    <div className="page">
      {/* Program bar */}
      {status.program_name && (
        <div style={{
          background: 'var(--blue-ghost)', borderRadius: 'var(--r)', padding: '12px 16px',
          marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '12px',
          border: '1px solid rgba(41,121,255,0.1)',
        }}>
          <div style={{ fontSize: '1.1rem' }}>📋</div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--blue)' }}>{status.program_name}</div>
            <div className="progress-bar" style={{ height: '5px', marginTop: '4px' }}>
              <div className="progress-bar-fill" style={{
                width: `${Math.round((status.program_day / status.program_total_days) * 100)}%`,
                background: 'var(--blue)',
              }} />
            </div>
          </div>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '0.85rem', color: 'var(--blue)', whiteSpace: 'nowrap' }}>
            {status.program_day}/{status.program_total_days}
          </div>
        </div>
      )}

      {/* === HERO: Today's Points === */}
      <div className={`gate-banner ${status.gate_passed ? 'gate-earned' : 'gate-locked'}`}>
        <div className="section-label" style={{ marginBottom: '4px' }}>
          <Tip text={`Hit ${status.daily_minimum} points to unlock your rewards for today. Points reset weekly. This is your daily "gate" — earn first, enjoy second.`}>
            Today
          </Tip>
        </div>
        <div className="gate-pts">
          <span style={{ color: status.gate_passed ? 'var(--green)' : 'var(--orange)' }}>
            {status.points_earned}
          </span>
          <span style={{ fontFamily: 'var(--font)', fontSize: '1rem', fontWeight: 600, color: 'var(--text-3)' }}>
            /{status.daily_minimum}
          </span>
        </div>
        <div className="progress-bar" style={{ marginTop: '12px', height: '12px' }}>
          <div className="progress-bar-fill" style={{
            width: `${pct}%`,
            background: status.gate_passed
              ? 'linear-gradient(90deg, #00C853, #69F0AE)'
              : `linear-gradient(90deg, #FF5722, #FF8A65)`,
          }} />
        </div>
        <div style={{ marginTop: '12px', fontSize: '0.88rem', fontWeight: 700 }}>
          {status.gate_passed
            ? <span style={{ color: 'var(--green-dark)' }}>✨ Rewards unlocked!</span>
            : <span style={{ color: 'var(--text-2)' }}>🔒 {status.points_remaining} more to unlock</span>
          }
        </div>
      </div>

      {/* === Quick Actions === */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '14px' }}>
        <button className="btn-primary btn-full" onClick={() => navigate('/log')}
          style={{ padding: '14px', fontSize: '0.9rem' }}>
          + Log Activity
        </button>
        <button className="btn-outline btn-full" onClick={() => navigate('/food')}
          style={{ padding: '14px', fontSize: '0.9rem' }}>
          🍽️ Log Food
        </button>
      </div>

      {/* === Activity Checklist === */}
      <div className="card">
        <div className="section-label">Activities</div>
        {activities.map(a => {
          const done = doneCats.has(a.key)
          return (
            <div className="checklist-item" key={a.key} style={{ opacity: done ? 1 : 0.6 }}>
              <span style={{
                width: '32px', height: '32px', borderRadius: '8px',
                background: done ? a.color : 'rgba(0,0,0,0.04)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '0.9rem', transition: 'all 0.3s',
              }}>{done ? '✓' : a.icon}</span>
              <span style={{ fontWeight: 600, fontSize: '0.88rem' }}>
                <Tip text={a.tip}>{a.label}</Tip>
              </span>
              <span className="checklist-points">+{a.pts}</span>
            </div>
          )
        })}
      </div>

      {/* === Week Progress === */}
      <div className="card" style={{ background: 'var(--purple-ghost)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <div className="section-label" style={{ margin: 0 }}>
            <Tip text={`Earn ${status.weekly_target} total points across the week for a bonus. Consistent daily effort beats one big day.`}>
              This Week
            </Tip>
          </div>
          <Link to="/week" style={{ fontSize: '0.8rem' }}>Details →</Link>
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginBottom: '8px' }}>
          <span style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '1.4rem' }}>
            {status.week_points}
          </span>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-3)', fontWeight: 600 }}>
            / {status.weekly_target} pts
          </span>
        </div>
        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${weekPct}%`, background: 'linear-gradient(90deg, #7C4DFF, #B388FF)' }} />
        </div>
      </div>

      {/* === Rewards === */}
      {status.gate_passed && status.rewards_available.length > 0 && (
        <div className="card" style={{ background: 'var(--green-ghost)', border: '2px solid rgba(0,200,83,0.15)' }}>
          <div className="section-label" style={{ color: 'var(--green-dark)' }}>🎮 Rewards Available</div>
          {status.rewards_available.map(r => (
            <div className="reward-card" key={r.id}>
              <div>
                <div style={{ fontWeight: 700 }}>{r.name}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-3)', fontWeight: 600 }}>{r.point_cost} pts</div>
              </div>
              <button className="btn-success btn-sm" onClick={async () => {
                try { await api.redeemReward(r.id); await loadAll() }
                catch (err) { alert(err.message) }
              }}>Redeem</button>
            </div>
          ))}
        </div>
      )}

      {/* === Integration Sync === */}
      <div className="card">
        <div className="section-label">
          <Tip text="Connect your fitness trackers to automatically import workouts. Go to Settings → Integrations to connect.">
            Integrations
          </Tip>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          {stravaConnected ? (
            <button className="btn-outline btn-sm btn-full" onClick={() => handleSync('strava')} disabled={syncing === 'strava'}>
              {syncing === 'strava' ? '⏳ Syncing...' : '🔄 Sync Strava'}
            </button>
          ) : (
            <button className="btn-ghost btn-sm btn-full" onClick={() => handleConnect('strava')}
              style={{ border: '2px dashed var(--divider)' }}>
              🔗 Connect Strava
            </button>
          )}
          {polarConnected ? (
            <button className="btn-outline btn-sm btn-full" onClick={() => handleSync('polar')} disabled={syncing === 'polar'}>
              {syncing === 'polar' ? '⏳ Syncing...' : '🔄 Sync Polar'}
            </button>
          ) : (
            <button className="btn-ghost btn-sm btn-full" onClick={() => handleConnect('polar')}
              style={{ border: '2px dashed var(--divider)' }}>
              🔗 Connect Polar
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
