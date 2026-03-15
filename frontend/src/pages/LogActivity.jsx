import { useState } from 'react'
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
  const navigate = useNavigate()

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
