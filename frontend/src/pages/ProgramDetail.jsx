import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api'

export default function ProgramDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [schedule, setSchedule] = useState(null)
  const [progress, setProgress] = useState(null)
  const [loading, setLoading] = useState(true)
  const [completing, setCompleting] = useState(null) // workout id being completed
  const [showComplete, setShowComplete] = useState(null) // workout to show completion modal
  const [completionResult, setCompletionResult] = useState(null)

  useEffect(() => { loadData() }, [id])

  async function loadData() {
    try {
      const [sched, prog] = await Promise.all([
        api.getProgramSchedule(id),
        api.getProgramProgress(id),
      ])
      setSchedule(sched)
      setProgress(prog)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  async function handleComplete(workoutId) {
    setCompleting(workoutId)
    try {
      const result = await api.completeWorkout(id, workoutId, {})
      setCompletionResult(result)
      setShowComplete(null)
      await loadData()
    } catch (err) {
      alert(err.message)
    }
    finally { setCompleting(null) }
  }

  if (loading) return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-3)' }}>Loading...</div>
  if (!schedule) return <div style={{ padding: '2rem', textAlign: 'center' }}>Program not found</div>

  const pct = progress ? progress.completion_pct : 0

  return (
    <div style={{ padding: '1rem', paddingBottom: '96px', maxWidth: '600px', margin: '0 auto' }}>
      {/* Back */}
      <button onClick={() => navigate('/programs')} style={{
        background: 'transparent', color: 'var(--text-3)', padding: '8px 0',
        fontSize: '0.85rem', marginBottom: '0.5rem',
      }}>← Programs</button>

      {/* Header */}
      <div style={{
        background: 'var(--card)', borderRadius: 'var(--r-lg)', padding: '20px',
        boxShadow: 'var(--shadow-2)', marginBottom: '1.5rem',
      }}>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', fontWeight: 900 }}>
          {schedule.program_name}
        </h1>
        <div style={{ display: 'flex', gap: '1.5rem', marginTop: '10px', fontSize: '0.82rem', color: 'var(--text-2)' }}>
          <span>Week {schedule.current_week}</span>
          <span>{progress?.completed_workouts || 0}/{progress?.total_workouts || 0} workouts</span>
          <span style={{ color: 'var(--orange)', fontWeight: 700 }}>{pct}%</span>
        </div>
        {/* Progress bar */}
        <div style={{ marginTop: '12px', height: '8px', borderRadius: '4px', background: 'var(--divider)' }}>
          <div style={{
            height: '100%', borderRadius: '4px',
            background: pct >= 100 ? 'var(--green)' : 'var(--orange)',
            width: `${Math.min(100, pct)}%`, transition: 'width 0.4s ease',
          }} />
        </div>
        {schedule.progression_rules && (
          <p style={{
            marginTop: '12px', fontSize: '0.8rem', color: 'var(--text-3)',
            lineHeight: 1.5, borderTop: '1px solid var(--divider)', paddingTop: '12px',
          }}>
            📈 {schedule.progression_rules}
          </p>
        )}
      </div>

      {/* Completion celebration */}
      {completionResult && (
        <div style={{
          background: 'var(--green-ghost)', borderRadius: 'var(--r)', padding: '16px',
          marginBottom: '1rem', textAlign: 'center',
        }}>
          <div style={{ fontSize: '1.8rem', marginBottom: '4px' }}>🎉</div>
          <strong style={{ color: 'var(--green-dark)' }}>
            +{completionResult.total_points} points!
          </strong>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-2)', marginTop: '4px' }}>
            Workout: +{completionResult.points_earned}
            {completionResult.weekly_bonus > 0 && ` • Week bonus: +${completionResult.weekly_bonus}`}
            {completionResult.completion_bonus > 0 && ` • Program complete: +${completionResult.completion_bonus}!`}
          </div>
          <button onClick={() => setCompletionResult(null)} style={{
            marginTop: '10px', background: 'transparent', color: 'var(--green-dark)',
            fontSize: '0.8rem', padding: '6px 16px', border: '1px solid var(--green)',
          }}>Dismiss</button>
        </div>
      )}

      {/* Today's Workout */}
      {schedule.today_workout && !schedule.today_workout.completed && !schedule.today_workout.rest_day && (
        <div style={{
          background: 'var(--card)', borderRadius: 'var(--r)', padding: '16px',
          marginBottom: '1.5rem', boxShadow: 'var(--shadow-2)',
          border: '2px solid var(--orange-glow)',
        }}>
          <div style={{
            fontSize: '0.72rem', fontWeight: 700, color: 'var(--orange)',
            textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px',
          }}>Today's Workout</div>
          <strong style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem' }}>
            {schedule.today_workout.workout_name || `Day ${schedule.today_workout.day_number}`}
          </strong>
          <div style={{ marginTop: '12px' }}>
            {(schedule.today_workout.exercises || []).map((ex, i) => (
              <ExerciseRow key={i} exercise={ex} />
            ))}
          </div>
          <button
            onClick={() => handleComplete(schedule.today_workout.id)}
            disabled={completing === schedule.today_workout.id}
            style={{
              marginTop: '14px', width: '100%', padding: '14px',
              background: completing ? 'var(--text-3)' : 'var(--green)',
              color: '#fff', fontSize: '0.95rem', fontWeight: 800,
              boxShadow: 'var(--shadow-green)',
            }}
          >
            {completing === schedule.today_workout.id ? 'Logging...' : '✓ Complete Workout — 75 pts'}
          </button>
        </div>
      )}

      {/* Full Schedule */}
      <h2 style={{
        fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 800,
        marginBottom: '0.75rem',
      }}>Full Schedule</h2>

      {groupByWeek(schedule.schedule).map(([week, workouts]) => (
        <div key={week} style={{ marginBottom: '1.25rem' }}>
          <div style={{
            fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-3)',
            textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.5rem',
            display: 'flex', alignItems: 'center', gap: '0.5rem',
          }}>
            Week {week}
            {week === schedule.current_week && (
              <span style={{
                fontSize: '0.65rem', background: 'var(--orange)', color: '#fff',
                padding: '2px 8px', borderRadius: 'var(--r-full)',
              }}>Current</span>
            )}
          </div>

          {workouts.map(w => (
            <div key={w.id} style={{
              background: 'var(--card)', borderRadius: 'var(--r-sm)', padding: '12px 14px',
              marginBottom: '0.4rem', boxShadow: 'var(--shadow-1)',
              opacity: w.completed ? 0.7 : 1,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <div>
                <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                  {w.rest_day ? '😴 Rest Day' : (w.workout_name || `Day ${w.day_number}`)}
                </span>
                {!w.rest_day && (
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-3)', marginLeft: '8px' }}>
                    {(w.exercises || []).length} exercises
                  </span>
                )}
              </div>
              <div>
                {w.completed ? (
                  <span style={{ color: 'var(--green)', fontSize: '0.85rem', fontWeight: 700 }}>✓</span>
                ) : !w.rest_day ? (
                  <button
                    onClick={() => setShowComplete(w)}
                    style={{
                      background: 'var(--green-ghost)', color: 'var(--green-dark)',
                      padding: '6px 12px', fontSize: '0.75rem', fontWeight: 700,
                    }}
                  >
                    Do it
                  </button>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      ))}

      {/* Workout Detail Modal */}
      {showComplete && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'flex-end', justifyContent: 'center', zIndex: 100,
        }} onClick={() => setShowComplete(null)}>
          <div style={{
            background: 'var(--card)', borderRadius: 'var(--r-lg) var(--r-lg) 0 0',
            padding: '24px 20px', width: '100%', maxWidth: '600px', maxHeight: '80vh',
            overflow: 'auto',
          }} onClick={e => e.stopPropagation()}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', fontWeight: 800, marginBottom: '4px' }}>
              {showComplete.workout_name || `Week ${showComplete.week_number}, Day ${showComplete.day_number}`}
            </h3>
            <p style={{ color: 'var(--text-3)', fontSize: '0.82rem', marginBottom: '16px' }}>
              Complete the exercises below and tap "Done" when finished.
            </p>

            {(showComplete.exercises || []).map((ex, i) => (
              <ExerciseRow key={i} exercise={ex} detailed />
            ))}

            {showComplete.notes && (
              <p style={{
                marginTop: '12px', fontSize: '0.8rem', color: 'var(--text-2)',
                background: 'var(--blue-ghost)', padding: '10px 12px', borderRadius: 'var(--r-sm)',
              }}>
                💡 {showComplete.notes}
              </p>
            )}

            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '20px' }}>
              <button onClick={() => setShowComplete(null)} style={{
                flex: 1, background: 'var(--divider)', color: 'var(--text-2)', padding: '14px',
              }}>Cancel</button>
              <button
                onClick={() => handleComplete(showComplete.id)}
                disabled={completing === showComplete.id}
                style={{
                  flex: 2, background: 'var(--green)', color: '#fff', padding: '14px',
                  fontWeight: 800, boxShadow: 'var(--shadow-green)',
                }}
              >
                {completing === showComplete.id ? 'Logging...' : '✓ Done — 75 pts'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


function ExerciseRow({ exercise, detailed }) {
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: detailed ? '10px 0' : '6px 0',
      borderBottom: '1px solid var(--divider)',
    }}>
      <div>
        <span style={{ fontWeight: 600, fontSize: detailed ? '0.9rem' : '0.82rem' }}>
          {exercise.name}
        </span>
        {detailed && exercise.notes && (
          <div style={{ fontSize: '0.75rem', color: 'var(--text-3)', marginTop: '2px' }}>
            {exercise.notes}
          </div>
        )}
        {detailed && exercise.weight_instruction && (
          <div style={{ fontSize: '0.75rem', color: 'var(--blue)', marginTop: '2px' }}>
            🏋️ {exercise.weight_instruction}
          </div>
        )}
      </div>
      <div style={{
        textAlign: 'right', fontSize: '0.8rem', color: 'var(--text-2)', fontWeight: 600,
        whiteSpace: 'nowrap',
      }}>
        {exercise.sets && exercise.reps && `${exercise.sets}×${exercise.reps}`}
        {exercise.rest_seconds && detailed && (
          <div style={{ fontSize: '0.7rem', color: 'var(--text-3)' }}>
            {exercise.rest_seconds >= 60
              ? `${Math.floor(exercise.rest_seconds / 60)}m rest`
              : `${exercise.rest_seconds}s rest`}
          </div>
        )}
      </div>
    </div>
  )
}


function groupByWeek(schedule) {
  const groups = {}
  for (const w of (schedule || [])) {
    const week = w.week_number
    if (!groups[week]) groups[week] = []
    groups[week].push(w)
  }
  return Object.entries(groups).sort(([a], [b]) => Number(a) - Number(b))
}
