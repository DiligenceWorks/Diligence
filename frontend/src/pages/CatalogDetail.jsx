import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api'

const DIFFICULTY_COLORS = {
  beginner: 'var(--green)',
  intermediate: 'var(--blue)',
  advanced: 'var(--purple)',
}

const CATEGORY_ICONS = {
  strength: '🏋️',
  cardio: '🏃',
  flexibility: '🧘',
  hybrid: '⚡',
}

const STATUS_LABELS = {
  pending: { label: 'Queued', color: 'var(--amber)' },
  crawling: { label: 'Fetching...', color: 'var(--blue)' },
  extracting: { label: 'Analyzing...', color: 'var(--purple)' },
  ready: { label: 'Ready', color: 'var(--green)' },
  failed: { label: 'Failed', color: 'var(--red)' },
}

export default function CatalogDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [program, setProgram] = useState(null)
  const [userPrograms, setUserPrograms] = useState([])
  const [loading, setLoading] = useState(true)
  const [adopting, setAdopting] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => { loadData() }, [id])

  async function loadData() {
    setLoading(true)
    try {
      const [p, mine] = await Promise.all([
        api.getCatalogProgram(id),
        api.listPrograms(),
      ])
      setProgram(p)
      setUserPrograms(mine)
    } catch (err) {
      setMessage({ type: 'error', text: err.message || 'Could not load program' })
    } finally {
      setLoading(false)
    }
  }

  async function handleAdopt() {
    setAdopting(true)
    setMessage(null)
    const today = new Date().toISOString().slice(0, 10)
    try {
      const result = await api.adoptProgram(id, today)
      setMessage({ type: 'success', text: 'Program started! Redirecting…' })
      setTimeout(() => navigate(`/programs/${result.id}`), 800)
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
      setAdopting(false)
    }
  }

  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-3)' }}>Loading...</div>
  }
  if (!program) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-2)', marginBottom: '1rem' }}>Program not found.</p>
        <button onClick={() => navigate('/programs')} style={{
          background: 'var(--blue)', color: '#fff', padding: '10px 20px',
        }}>← Back to Programs</button>
      </div>
    )
  }

  const adopted = userPrograms.some(p => p.status === 'active' && p.catalog_id === program.id)
  const activeRecord = userPrograms.find(p => p.status === 'active' && p.catalog_id === program.id)
  const status = STATUS_LABELS[program.crawl_status] || STATUS_LABELS.pending
  const groupedWorkouts = groupByWeek(program.workouts)

  return (
    <div style={{ padding: '1rem', paddingBottom: '96px', maxWidth: '600px', margin: '0 auto' }}>
      {/* Back */}
      <button onClick={() => navigate('/programs')} style={{
        background: 'transparent', color: 'var(--text-3)', padding: '8px 0',
        fontSize: '0.85rem', marginBottom: '0.5rem',
      }}>← Programs</button>

      {/* Header card */}
      <div style={{
        background: 'var(--card)', borderRadius: 'var(--r-lg)', padding: '20px',
        boxShadow: 'var(--shadow-2)', marginBottom: '1rem',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', fontWeight: 900, lineHeight: 1.2 }}>
            {CATEGORY_ICONS[program.category] || '📋'} {program.name}
          </h1>
          <span style={{
            fontSize: '0.7rem', fontWeight: 700, padding: '4px 10px',
            borderRadius: 'var(--r-full)', color: '#fff', background: status.color,
            whiteSpace: 'nowrap',
          }}>
            {status.label}
          </span>
        </div>

        {program.description && (
          <p style={{ color: 'var(--text-2)', fontSize: '0.88rem', marginTop: '12px', lineHeight: 1.5 }}>
            {program.description}
          </p>
        )}

        {/* Meta tags */}
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '14px' }}>
          {program.duration_weeks && (
            <span style={tagStyle}>{program.duration_weeks} weeks</span>
          )}
          {program.frequency_per_week && (
            <span style={tagStyle}>{program.frequency_per_week}x/week</span>
          )}
          {program.difficulty && (
            <span style={{
              ...tagStyle,
              color: DIFFICULTY_COLORS[program.difficulty] || 'var(--text-3)',
              background: `${DIFFICULTY_COLORS[program.difficulty] || 'var(--text-3)'}15`,
            }}>
              {program.difficulty}
            </span>
          )}
          {(program.equipment || []).map(eq => (
            <span key={eq} style={tagStyle}>{eq}</span>
          ))}
        </div>

        {program.source_url && (
          <a
            href={program.source_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-block', marginTop: '14px', fontSize: '0.78rem',
              color: 'var(--blue)', textDecoration: 'none',
            }}
          >
            🔗 Original source ↗
          </a>
        )}
      </div>

      {/* Message */}
      {message && (
        <div style={{
          padding: '12px 16px', borderRadius: 'var(--r-sm)', marginBottom: '1rem',
          fontSize: '0.85rem', fontWeight: 600,
          background: message.type === 'error' ? 'var(--red-ghost)' : 'var(--green-ghost)',
          color: message.type === 'error' ? 'var(--red)' : 'var(--green-dark)',
        }}>
          {message.text}
        </div>
      )}

      {/* Adopt button */}
      {program.crawl_status === 'ready' && !adopted && (
        <button
          onClick={handleAdopt}
          disabled={adopting}
          style={{
            width: '100%', background: adopting ? 'var(--text-3)' : 'var(--green)',
            color: '#fff', padding: '14px', fontSize: '0.95rem', fontWeight: 800,
            marginBottom: '1.25rem', boxShadow: adopting ? 'none' : 'var(--shadow-green)',
          }}
        >
          {adopting ? 'Starting...' : 'Start This Program'}
        </button>
      )}

      {adopted && activeRecord && (
        <button
          onClick={() => navigate(`/programs/${activeRecord.id}`)}
          style={{
            width: '100%', background: 'var(--orange)', color: '#fff',
            padding: '14px', fontSize: '0.95rem', fontWeight: 800,
            marginBottom: '1.25rem', boxShadow: 'var(--shadow-orange)',
          }}
        >
          ✓ Active — Open Your Program
        </button>
      )}

      {program.crawl_status !== 'ready' && (
        <div style={{
          padding: '14px', borderRadius: 'var(--r)', background: 'var(--blue-ghost)',
          color: 'var(--blue)', fontSize: '0.85rem', marginBottom: '1.25rem', textAlign: 'center',
        }}>
          {program.crawl_status === 'failed'
            ? `Crawl failed: ${program.crawl_error || 'unknown error'}`
            : 'Program is being researched. Check back soon.'}
        </div>
      )}

      {/* Progression rules */}
      {program.progression_rules && (
        <div style={{
          background: 'var(--card)', borderRadius: 'var(--r)', padding: '16px',
          marginBottom: '1.25rem', boxShadow: 'var(--shadow-1)',
        }}>
          <div style={{
            fontSize: '0.72rem', fontWeight: 700, color: 'var(--orange)',
            textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px',
          }}>📈 Progression</div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-2)', lineHeight: 1.5 }}>
            {program.progression_rules}
          </p>
        </div>
      )}

      {/* Workouts preview */}
      {groupedWorkouts.length > 0 && (
        <>
          <h2 style={{
            fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 800,
            marginBottom: '0.75rem',
          }}>
            Workouts
          </h2>

          {groupedWorkouts.map(([week, workouts]) => (
            <div key={week} style={{ marginBottom: '1.25rem' }}>
              <div style={{
                fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-3)',
                textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.5rem',
              }}>
                Week {week}
              </div>

              {workouts.map(w => (
                <div key={w.id} style={{
                  background: 'var(--card)', borderRadius: 'var(--r-sm)', padding: '14px',
                  marginBottom: '0.5rem', boxShadow: 'var(--shadow-1)',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: w.rest_day ? 0 : '8px' }}>
                    <strong style={{ fontSize: '0.92rem', fontFamily: 'var(--font-display)' }}>
                      {w.rest_day ? '😴 Rest Day' : (w.workout_name || `Day ${w.day_number}`)}
                    </strong>
                    {!w.rest_day && (
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-3)', fontWeight: 600 }}>
                        {(w.exercises || []).length} exercises
                      </span>
                    )}
                  </div>

                  {!w.rest_day && (w.exercises || []).map((ex, i) => (
                    <div key={i} style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      padding: '6px 0',
                      borderTop: i === 0 ? '1px solid var(--divider)' : 'none',
                      borderBottom: i < w.exercises.length - 1 ? '1px solid var(--divider)' : 'none',
                    }}>
                      <span style={{ fontSize: '0.82rem', color: 'var(--text-2)' }}>
                        {ex.name}
                      </span>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-3)', fontWeight: 600 }}>
                        {ex.sets && ex.reps && `${ex.sets}×${ex.reps}`}
                      </span>
                    </div>
                  ))}

                  {w.notes && (
                    <p style={{
                      marginTop: '8px', fontSize: '0.78rem', color: 'var(--text-3)',
                      borderTop: '1px solid var(--divider)', paddingTop: '8px',
                    }}>
                      💡 {w.notes}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ))}

          {program.duration_weeks && groupedWorkouts.length < program.duration_weeks && (
            <p style={{
              fontSize: '0.78rem', color: 'var(--text-3)', textAlign: 'center',
              padding: '12px', fontStyle: 'italic',
            }}>
              Showing {groupedWorkouts.length} of {program.duration_weeks} weeks — pattern repeats across the program.
            </p>
          )}
        </>
      )}
    </div>
  )
}

const tagStyle = {
  fontSize: '0.72rem', fontWeight: 600, padding: '3px 10px',
  borderRadius: 'var(--r-full)', background: 'var(--divider)', color: 'var(--text-2)',
}

function groupByWeek(workouts) {
  const groups = {}
  for (const w of (workouts || [])) {
    const week = w.week_number
    if (!groups[week]) groups[week] = []
    groups[week].push(w)
  }
  // Sort workouts within each week by day_number
  for (const week of Object.keys(groups)) {
    groups[week].sort((a, b) => a.day_number - b.day_number)
  }
  return Object.entries(groups).sort(([a], [b]) => Number(a) - Number(b))
}
