import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

const CATEGORIES = [
  { value: 'workout', label: 'Workout', icon: '💪', desc: 'Any exercise session' },
  { value: 'steps_target', label: 'Steps Target', icon: '👟', desc: 'Hit your daily step goal' },
  { value: 'screen_free', label: 'Screen-Free', icon: '📖', desc: 'Reading, outdoor time, etc.' },
  { value: 'daily_checkin', label: 'Daily Check-in', icon: '✅', desc: 'Just showing up counts' },
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
      setSuccess(`+${result.points_earned} points earned!`)
      setCategory(''); setTitle(''); setDuration(''); setDescription('')
      setTimeout(() => navigate('/'), 1500)
    } catch (err) { alert(err.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="page">
      <h1 className="page-title">Log Activity</h1>

      {success && (
        <div style={{ textAlign: 'center', padding: '24px', background: 'var(--success-bg)', borderRadius: 'var(--radius)', marginBottom: '16px', border: '1px solid rgba(34, 197, 94, 0.15)' }}>
          <div style={{ fontSize: '1.8rem', marginBottom: '4px' }}>🎉</div>
          <div style={{ color: 'var(--success)', fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.1rem' }}>{success}</div>
        </div>
      )}

      <div style={{ marginBottom: '20px' }}>
        <div className="form-label">What did you do?</div>
        <div className="option-grid">
          {CATEGORIES.map(c => (
            <div key={c.value} className={`option-btn ${category === c.value ? 'selected' : ''}`} onClick={() => setCategory(c.value)}>
              <div style={{ fontSize: '1.4rem', marginBottom: '6px' }}>{c.icon}</div>
              <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>{c.label}</div>
              <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)', marginTop: '3px', fontWeight: 400 }}>{c.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {category && (
        <form onSubmit={handleSubmit} className="card">
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
          <button type="submit" className="btn-primary btn-full" disabled={loading}>
            {loading ? 'Saving...' : 'Log Activity'}
          </button>
        </form>
      )}
    </div>
  )
}
