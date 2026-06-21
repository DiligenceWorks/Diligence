import { useState, useEffect } from 'react'
import { api } from '../api'

export default function WeekView() {
  const [week, setWeek] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { load() }, [])
  async function load() {
    try { setWeek(await api.week()) }
    catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  if (loading) return <div className="page"><div className="loading">Loading...</div></div>
  if (!week) return <div className="page"><div className="error-msg">Failed to load</div></div>

  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  const pct = week.weekly_target > 0 ? Math.min(100, Math.round((week.total_points_earned / week.weekly_target) * 100)) : 0
  const today = new Date().toISOString().split('T')[0]

  return (
    <div className="page">
      <h1 className="page-title">This Week</h1>

      {/* Summary hero */}
      <div className="card" style={{ textAlign: 'center', background: 'var(--accent-bg)' }}>
        <div className="section-label">Weekly Total</div>
        <div style={{ fontFamily: 'var(--font-display)', fontSize: '2.6rem', fontWeight: 900, letterSpacing: '-0.03em' }}>
          {week.total_points_earned}
        </div>
        <div style={{ color: 'var(--text-3)', fontWeight: 600, fontSize: '0.88rem', marginBottom: '12px' }}>
          / {week.weekly_target} pts
        </div>
        <div className="progress-bar" style={{ height: '12px' }}>
          <div className="progress-bar-fill" style={{
            width: `${pct}%`,
            background: week.hit_weekly_target ? 'linear-gradient(90deg, #00C853, #69F0AE)' : 'linear-gradient(90deg, #7C4DFF, #B388FF)',
          }} />
        </div>
        {week.hit_weekly_target && (
          <div style={{ marginTop: '10px', color: 'var(--green-dark)', fontWeight: 700, fontSize: '0.9rem' }}>
            🏆 Target hit! +{week.weekly_bonus_earned} bonus
          </div>
        )}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '28px', marginTop: '14px' }}>
          <div>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '1.3rem' }}>{week.active_days}</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-3)', fontWeight: 600 }}>active days</div>
          </div>
          <div>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '1.3rem' }}>{week.gate_passed_days}</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-3)', fontWeight: 600 }}>rewards earned</div>
          </div>
        </div>
      </div>

      {/* Daily breakdown */}
      <div className="card">
        <div className="section-label">Daily Breakdown</div>
        {week.daily_breakdown.map((day, i) => {
          const dayPct = day.daily_minimum > 0 ? Math.min(100, Math.round((day.points_earned / day.daily_minimum) * 100)) : 0
          const isToday = day.date === today
          return (
            <div key={day.date} style={{
              display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 0',
              borderBottom: i < 6 ? '1px solid var(--divider)' : 'none',
            }}>
              <div style={{
                width: '38px', fontWeight: isToday ? 800 : 600, fontSize: '0.85rem',
                color: isToday ? 'var(--accent)' : 'var(--text)',
              }}>
                {days[i]}
              </div>
              <div style={{ flex: 1 }}>
                <div className="progress-bar" style={{ height: '8px' }}>
                  <div className="progress-bar-fill" style={{
                    width: `${dayPct}%`,
                    background: day.gate_passed ? 'var(--green)' : day.points_earned > 0 ? 'var(--amber)' : 'transparent',
                  }} />
                </div>
              </div>
              <div style={{ width: '46px', textAlign: 'right', fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '0.9rem' }}>
                {day.points_earned}
              </div>
              <div style={{ width: '22px', textAlign: 'center', fontSize: '0.9rem' }}>
                {day.gate_passed ? '✅' : day.points_earned > 0 ? '🟡' : '⬜'}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
