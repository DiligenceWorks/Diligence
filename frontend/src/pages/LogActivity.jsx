import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

const CATEGORIES = [
  { value: 'workout', label: 'Workout', icon: '💪', desc: 'Any exercise session', color: '#FF5722' },
  { value: 'steps_target', label: 'Steps', icon: '👟', desc: 'Hit your daily goal', color: '#2979FF' },
  { value: 'screen_free', label: 'Screen-Free', icon: '📖', desc: 'Reading, outdoors', color: '#7C4DFF' },
  { value: 'daily_checkin', label: 'Check-in', icon: '✅', desc: 'Just show up', color: '#00BCD4' },
]

export default function LogActivity() {
  const [category, setCategory] = useState('')
  const [title, setTitle] = useState('')
  const [duration, setDuration] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState('')

  // Active program + today's workout (for the quick-log card)
  const [activeProgram, setActiveProgram] = useState(null)
  const [todayWorkout, setTodayWorkout] = useState(null)
  const [completingProgramWorkout, setCompletingProgramWorkout] = useState(false)

  const navigate = useNavigate()

  useEffect(() => { loadProgramWorkout() }, [])

  async function loadProgramWorkout() {
    try {
      const programs = await api.listPrograms()
      const active = (programs || []).find(p => p.status === 'active' && p.catalog_id)
      if (!active) return
      setActiveProgram(active)
      const schedule = await api.getProgramSchedule(active.id)
      if (schedule.today_workout && !schedule.today_workout.rest_day && !schedule.today_workout.completed) {
        setTodayWorkout(schedule.today_workout)
      }
    } catch (err) {
      // Silently ignore — page should still work without the program shortcut
      console.warn('Could not load active program:', err.message)
    }
  }

  async function handleCompleteProgramWorkout() {
    if (!activeProgram || !todayWorkout || completingProgramWorkout) return
    setCompletingProgramWorkout(true)
    try {
      const result = await api.completeWorkout(activeProgram.id, todayWorkout.id, {})
      const totalPts = result.total_points || result.points_earned
      let msg = `+${totalPts} points!`
      if (result.weekly_bonus > 0) msg += ' (week bonus!)'
      if (result.completion_bonus > 0) msg += ' (program complete!)'
      setSuccess(msg)
      setTimeout(() => navigate('/'), 1500)
    } catch (err) {
      alert(err.message)
      setCompletingProgramWorkout(false)
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!category) return
    setLoading(true)
    try {
      const today = new Date().toISOString().split('T')[0]
      const result = await api.logActivity({
        category,
        title: title || CATEGORIES.find(c => c.value === category)?.label,
        description: description || null,
        duration_minutes: duration ? parseInt(duration) : null,
        activity_date: today,
      })
      setSuccess(`+${result.points_earned} points!`)
      setCategory(''); setTitle(''); setDuration(''); setDescription('')
      setTimeout(() => navigate('/'), 1200)
    } catch (err) { alert(err.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="page">
      <h1 className="page-title">Log Activity</h1>

      {success && (
        <div style={{
          textAlign: 'center', padding: '24px', marginBottom: '14px',
          background: 'var(--green-ghost)', borderRadius: 'var(--r-lg)', border: '2px solid rgba(0,200,83,0.15)',
        }}>
          <div style={{ fontSize: '2rem', marginBottom: '4px' }}>🎉</div>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '1.3rem', color: 'var(--green-dark)' }}>{success}</div>
        </div>
      )}

      {/* Today's program workout — featured shortcut */}
      {!success && todayWorkout && activeProgram && (
        <div style={{
          background: 'var(--card)', borderRadius: 'var(--r-lg)', padding: '18px',
          marginBottom: '18px', border: '2px solid var(--orange-glow)',
          boxShadow: 'var(--shadow-2)',
        }}>
          <div style={{
            fontSize: '0.7rem', fontWeight: 800, color: 'var(--orange)',
            textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px',
          }}>
            ⭐ Today's Program Workout
          </div>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.05rem', marginBottom: '2px' }}>
            {todayWorkout.workout_name || `Day ${todayWorkout.day_number}`}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-3)', marginBottom: '12px' }}>
            {activeProgram.name} · Week {todayWorkout.week_number} · {(todayWorkout.exercises || []).length} exercises
          </div>

          {/* Exercise preview */}
          <div style={{
            background: 'var(--bg-warm)', borderRadius: 'var(--r-sm)', padding: '10px 12px',
            marginBottom: '12px',
          }}>
            {(todayWorkout.exercises || []).slice(0, 4).map((ex, i) => (
              <div key={i} style={{
                display: 'flex', justifyContent: 'space-between',
                fontSize: '0.78rem', padding: '3px 0',
                color: 'var(--text-2)',
              }}>
                <span>{ex.name}</span>
                <span style={{ color: 'var(--text-3)', fontWeight: 600 }}>
                  {ex.sets && ex.reps && `${ex.sets}×${ex.reps}`}
                </span>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={handleCompleteProgramWorkout}
              disabled={completingProgramWorkout}
              style={{
                flex: 2, background: completingProgramWorkout ? 'var(--text-3)' : 'var(--green)',
                color: '#fff', padding: '12px', fontWeight: 800, fontSize: '0.9rem',
                boxShadow: completingProgramWorkout ? 'none' : 'var(--shadow-green)',
              }}
            >
              {completingProgramWorkout ? 'Logging...' : '✓ Complete — 75 pts'}
            </button>
            <button
              onClick={() => navigate(`/programs/${activeProgram.id}`)}
              style={{
                flex: 1, background: 'transparent', color: 'var(--blue)',
                padding: '12px', fontSize: '0.85rem', fontWeight: 700,
                border: '1px solid var(--divider)',
              }}
            >
              Details
            </button>
          </div>
        </div>
      )}

      <div style={{ marginBottom: '18px' }}>
        <div className="section-label">
          {todayWorkout ? 'Or log something else' : 'What did you do?'}
        </div>
        <div className="option-grid">
          {CATEGORIES.map(c => (
            <div key={c.value} className={`option-btn ${category === c.value ? 'selected' : ''}`}
              onClick={() => setCategory(c.value)}
              style={category === c.value ? { borderColor: c.color, background: c.color + '0A' } : {}}>
              <div style={{ fontSize: '1.5rem', marginBottom: '6px' }}>{c.icon}</div>
              <div style={{ fontWeight: 800, fontSize: '0.85rem' }}>{c.label}</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-3)', marginTop: '2px', fontWeight: 400 }}>{c.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {category && (
        <form onSubmit={handleSubmit} className="card" style={{ animation: 'fadeUp 0.25s ease-out' }}>
          <div className="form-group">
            <label className="form-label">Title (optional)</label>
            <input value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Morning run, StrongLifts Day 12" />
          </div>
          {(category === 'workout' || category === 'screen_free') && (
            <div className="form-group">
              <label className="form-label">Duration (minutes)</label>
              <input type="number" value={duration} onChange={e => setDuration(e.target.value)} placeholder="30" />
            </div>
          )}
          <div className="form-group">
            <label className="form-label">Notes (optional)</label>
            <textarea value={description} onChange={e => setDescription(e.target.value)} rows={2} placeholder="How did it go?" />
          </div>
          <button type="submit" className="btn-primary btn-full" disabled={loading} style={{ borderRadius: 'var(--r)' }}>
            {loading ? 'Saving...' : 'Log Activity'}
          </button>
        </form>
      )}
    </div>
  )
}
