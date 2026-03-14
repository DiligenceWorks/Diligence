import { useState, useEffect } from 'react'
import { api } from '../api'

export default function Rewards() {
  const [rewards, setRewards] = useState([])
  const [newName, setNewName] = useState('')
  const [newCost, setNewCost] = useState('100')
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { load() }, [])

  async function load() {
    try {
      const [r, s] = await Promise.all([api.listRewards(), api.today()])
      setRewards(r)
      setStatus(s)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  async function handleCreate(e) {
    e.preventDefault()
    if (!newName.trim()) return
    try {
      await api.createReward({ name: newName, point_cost: parseInt(newCost) || 100 })
      setNewName(''); setNewCost('100')
      await load()
    } catch (err) { alert(err.message) }
  }

  async function handleRedeem(id) {
    try {
      await api.redeemReward(id)
      await load()
    } catch (err) { alert(err.message) }
  }

  if (loading) return <div className="page"><div className="loading">Loading...</div></div>

  return (
    <div className="page">
      <h1 className="page-title">🎮 Rewards</h1>

      {/* Status */}
      {status && (
        <div className={`gate-banner ${status.gate_passed ? 'gate-earned' : 'gate-locked'}`} style={{ marginBottom: '16px' }}>
          <div style={{ fontWeight: 700 }}>
            {status.gate_passed ? '✅ Rewards Unlocked' : `🔒 Earn ${status.points_remaining} more pts`}
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            {status.points_earned} / {status.daily_minimum} pts today
          </div>
        </div>
      )}

      {/* Reward list */}
      <div className="card">
        {rewards.length === 0 && <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '16px' }}>No rewards yet. Add one below!</div>}
        {rewards.map(r => (
          <div className="reward-card" key={r.id}>
            <div>
              <div style={{ fontWeight: 600 }}>{r.name}</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{r.point_cost} pts</div>
            </div>
            <button
              className={status?.gate_passed ? 'btn-success btn-sm' : 'btn-outline btn-sm'}
              disabled={!status?.gate_passed}
              onClick={() => handleRedeem(r.id)}
            >
              {status?.gate_passed ? 'Redeem' : 'Locked'}
            </button>
          </div>
        ))}
      </div>

      {/* Add new reward */}
      <div className="card">
        <div style={{ fontWeight: 700, marginBottom: '12px', fontSize: '0.9rem' }}>Add New Reward</div>
        <form onSubmit={handleCreate}>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '10px', marginBottom: '10px' }}>
            <input value={newName} onChange={e => setNewName(e.target.value)} placeholder="e.g. 1hr gaming" required />
            <input type="number" value={newCost} onChange={e => setNewCost(e.target.value)} placeholder="pts" />
          </div>
          <button type="submit" className="btn-primary btn-full btn-sm">Add Reward</button>
        </form>
      </div>
    </div>
  )
}
