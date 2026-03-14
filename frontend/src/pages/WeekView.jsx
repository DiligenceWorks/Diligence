import { useState, useEffect } from 'react'
import { api } from '../api'

export default function WeekView() {
  const [week, setWeek] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { load() }, [])

  async function load() {
    try {
      const data = await api.week()
      setWeek(data)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  if (loading) return <div className="page"><div className="loading">Loading...</div></div>
  if (!week) return <div className="page"><div className="error-msg">Failed to load</div></div>

  const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  const pct = week.weekly_target > 0 ? Math.min(100, Math.round((week.total_points_earned / week.weekly_target) * 100)) : 0

  return (
    <div className="page">
      <h1 className="page-title">📊 This Week</h1>

      {/* Week summary */}
      <div className="card" style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '2rem', fontWeight: 800 }}>{week.total_points_earned}</div>
        <div style={{ color: 'var(--text-muted)', marginBottom: '8px' }}>/ {week.weekly_target} pts</div>
        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${pct}%`, background: week.hit_weekly_target ? 'var(--success)' : 'var(--accent)' }} />
        </div>
        {week.hit_weekly_target && (
          <div style={{ marginTop: '8px', color: 'var(--success)', fontWeight: 600 }}>
            🏆 Weekly target hit! +{week.weekly_bonus_earned} bonus pts
          </div>
        )}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '24px', marginTop: '12px', fontSize: '0.85rem' }}>
          <div><span style={{ fontWeight: 700 }}>{week.active_days}</span> <span style={{ color: 'var(--text-muted)' }}>active days</span></div>
          <div><span style={{ fontWeight: 700 }}>{week.gate_passed_days}</span> <span style={{ color: 'var(--text-muted)' }}>rewards earned</span></div>
        </div>
      </div>

      {/* Daily breakdown */}
      <div className="card">
        <div style={{ fontWeight: 700, marginBottom: '12px' }}>Daily Breakdown</div>
        {week.daily_breakdown.map((day, i) => {
          const dayPct = day.daily_minimum > 0 ? Math.min(100, Math.round((day.points_earned / day.daily_minimum) * 100)) : 0
          const isToday = day.date === new Date().toISOString().split('T')[0]
          return (
            <div key={day.date} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 0', borderBottom: i < 6 ? '1px solid var(--border)' : 'none' }}>
              <div style={{ width: '40px', fontWeight: isToday ? 700 : 400, color: isToday ? 'var(--accent)' : 'var(--text)' }}>
                {dayNames[i]}
              </div>
              <div style={{ flex: 1 }}>
                <div className="progress-bar" style={{ height: '6px' }}>
                  <div className="progress-bar-fill" style={{
                    width: `${dayPct}%`,
                    background: day.gate_passed ? 'var(--success)' : day.points_earned > 0 ? 'var(--warning)' : 'var(--border)',
                  }} />
                </div>
              </div>
              <div style={{ width: '50px', textAlign: 'right', fontSize: '0.85rem', fontWeight: 600 }}>
                {day.points_earned}
              </div>
              <div style={{ width: '24px', textAlign: 'center' }}>
                {day.gate_passed ? '✅' : day.points_earned > 0 ? '🟡' : '⬜'}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
