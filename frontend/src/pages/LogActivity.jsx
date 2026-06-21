import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

const CATEGORIES = [
  { value: 'workout', label: 'Workout', icon: '💪', desc: 'Any exercise session', color: 'var(--accent)' },
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

  // Active program + schedule (loaded once on mount, used when category=workout)
  const [activeProgram, setActiveProgram] = useState(null)
  const [todayWorkout, setTodayWorkout] = useState(null)
  const [upcomingWorkouts, setUpcomingWorkouts] = useState([])
  const [completingProgramWorkout, setCompletingProgramWorkout] = useState(null)

  const navigate = useNavigate()

  useEffect(() => { loadActiveProgram() }, [])

  async function loadActiveProgram() {
    try {
      const programs = await api.listPrograms()
      const active = (programs || []).find(p => p.status === 'active' && p.catalog_id)
      if (!active) return
      setActiveProgram(active)

      const schedule = await api.getProgramSchedule(active.id)
      // Today's workout (highlighted)
      if (schedule.today_workout && !schedule.today_workout.rest_day && !schedule.today_workout.completed) {
        setTodayWorkout(schedule.today_workout)
      }
      // Upcoming uncompleted workouts in current week (in case there are several to choose from)
      const upcoming = (schedule.schedule || [])
        .filter(w =>
          w.week_number === schedule.current_week &&
          !w.rest_day &&
          !w.completed &&
          w.id !== schedule.today_workout?.id
        )
        .slice(0, 3)
      setUpcomingWorkouts(upcoming)
    } catch (err) {
      console.warn('Could not load active program:', err.message)
    }
  }

  async function handleCompleteProgramWorkout(workout) {
    if (!activeProgram || !workout || completingProgramWorkout) return
    setCompletingProgramWorkout(workout.id)
    try {
      const result = await api.completeWorkout(activeProgram.id, workout.id, {})
      const totalPts = result.total_points || result.points_earned
      let msg = `+${totalPts} points!`
      if (result.weekly_bonus > 0) msg += ' (week bonus!)'
      if (result.completion_bonus > 0) msg += ' (program complete!)'
      setSuccess(msg)
      setTimeout(() => navigate('/'), 1500)
    } catch (err) {
      alert(err.message)
      setCompletingProgramWorkout(null)
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

  const showProgramOptions = category === 'workout' && activeProgram

  return (
    <div className="page">
      <h1 className="page-title">Log Activity</h1>

      {success && (
        <div style={{
          textAlign: 'center', padding: '24px', marginBottom: '14px',
          background: 'var(--green-bg)', borderRadius: 'var(--r-lg)', border: '2px solid rgba(0,200,83,0.15)',
        }}>
          <div style={{ fontSize: '2rem', marginBottom: '4px' }}>🎉</div>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '1.3rem', color: 'var(--green-dark)' }}>{success}</div>
        </div>
      )}

      <div style={{ marginBottom: '18px' }}>
        <div className="section-label">What did you do?</div>
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

      {/* Program workout options — only when "Workout" category is selected */}
      {showProgramOptions && (
        <div style={{ animation: 'fadeUp 0.25s ease-out', marginBottom: '18px' }}>
          {/* Active program banner */}
          <div
            onClick={() => navigate(`/programs/${activeProgram.id}`)}
            style={{
              background: 'var(--accent-bg)', borderRadius: 'var(--r-sm)', padding: '10px 14px',
              marginBottom: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              cursor: 'pointer', border: '1px solid rgba(41,121,255,0.15)',
            }}
          >
            <div>
              <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Active Program
              </div>
              <div style={{ fontWeight: 800, fontSize: '0.92rem', color: 'var(--text-1)' }}>
                {activeProgram.name}
              </div>
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--accent)', fontWeight: 700 }}>
              Week {activeProgram.current_week || 1} →
            </div>
          </div>

          {/* Today's workout — featured */}
          {todayWorkout && (
            <ProgramWorkoutCard
              workout={todayWorkout}
              featured
              completing={completingProgramWorkout === todayWorkout.id}
              onComplete={() => handleCompleteProgramWorkout(todayWorkout)}
            />
          )}

          {/* Other uncompleted workouts in current week */}
          {upcomingWorkouts.length > 0 && (
            <>
              <div className="section-label" style={{ marginTop: '14px', marginBottom: '8px' }}>
                {todayWorkout ? 'Or another from this week' : 'Workouts this week'}
              </div>
              {upcomingWorkouts.map(w => (
                <ProgramWorkoutCard
                  key={w.id}
                  workout={w}
                  completing={completingProgramWorkout === w.id}
                  onComplete={() => handleCompleteProgramWorkout(w)}
                />
              ))}
            </>
          )}

          {!todayWorkout && upcomingWorkouts.length === 0 && (
            <div style={{
              padding: '14px', borderRadius: 'var(--r-sm)', background: 'var(--green-bg)',
              color: 'var(--green-dark)', fontSize: '0.85rem', textAlign: 'center', fontWeight: 600,
            }}>
              ✓ All workouts for this week are complete. Log a freeform workout below or rest up.
            </div>
          )}

          <div style={{
            textAlign: 'center', color: 'var(--text-3)', fontSize: '0.78rem',
            margin: '14px 0 6px', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700,
          }}>
            — or log freeform —
          </div>
        </div>
      )}

      {category && (
        <form onSubmit={handleSubmit} className="card" style={{ animation: 'fadeUp 0.25s ease-out' }}>
          <div className="form-group">
            <label className="form-label">Title (optional)</label>
            <input value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Morning run, evening yoga" />
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


function ProgramWorkoutCard({ workout, featured, completing, onComplete }) {
  return (
    <div style={{
      background: 'var(--card)', borderRadius: 'var(--r)', padding: '14px',
      marginBottom: '10px', boxShadow: 'var(--shadow-1)',
      border: featured ? '2px solid var(--accent-glow)' : '1px solid var(--divider)',
    }}>
      {featured && (
        <div style={{
          fontSize: '0.65rem', fontWeight: 800, color: 'var(--accent)',
          textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px',
        }}>
          ⭐ Today
        </div>
      )}
      <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1rem', marginBottom: '2px' }}>
        {workout.workout_name || `Day ${workout.day_number}`}
      </div>
      <div style={{ fontSize: '0.74rem', color: 'var(--text-3)', marginBottom: '10px' }}>
        Week {workout.week_number} · Day {workout.day_number} · {(workout.exercises || []).length} exercises
      </div>

      {/* Exercise preview */}
      <div style={{
        background: 'var(--bg-warm)', borderRadius: 'var(--r-sm)', padding: '8px 10px',
        marginBottom: '10px',
      }}>
        {(workout.exercises || []).slice(0, 4).map((ex, i) => (
          <div key={i} style={{
            display: 'flex', justifyContent: 'space-between',
            fontSize: '0.76rem', padding: '2px 0', color: 'var(--text-2)',
          }}>
            <span>{ex.name}</span>
            <span style={{ color: 'var(--text-3)', fontWeight: 600 }}>
              {ex.sets && ex.reps && `${ex.sets}×${ex.reps}`}
            </span>
          </div>
        ))}
      </div>

      <button
        onClick={onComplete}
        disabled={completing}
        style={{
          width: '100%', background: completing ? 'var(--text-3)' : 'var(--green)',
          color: '#fff', padding: '11px', fontWeight: 800, fontSize: '0.88rem',
          boxShadow: completing ? 'none' : 'var(--shadow-green)',
        }}
      >
        {completing ? 'Logging...' : '✓ Complete — 75 pts'}
      </button>
    </div>
  )
}
