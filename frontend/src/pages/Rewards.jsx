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
    try { const [r, s] = await Promise.all([api.listRewards(), api.today()]); setRewards(r); setStatus(s) }
    catch (err) { console.error(err) }
    finally { setLoading(false) }
  }
  async function handleCreate(e) {
    e.preventDefault()
    if (!newName.trim()) return
    try { await api.createReward({ name: newName, point_cost: parseInt(newCost) || 100 }); setNewName(''); setNewCost('100'); await load() }
    catch (err) { alert(err.message) }
  }
  async function handleRedeem(id) {
    try { await api.redeemReward(id); await load() }
    catch (err) { alert(err.message) }
  }

  if (loading) return <div className="page"><div className="loading">Loading...</div></div>

  return (
    <div className="page">
      <h1 className="page-title">🎮 Rewards</h1>

      {/* Status banner */}
      {status && (
        <div className={`gate-banner ${status.gate_passed ? 'gate-earned' : 'gate-locked'}`} style={{ padding: '18px', marginBottom: '14px' }}>
          <div style={{ fontWeight: 800, fontSize: '1rem', fontFamily: 'var(--font-display)' }}>
            {status.gate_passed
              ? <span style={{ color: 'var(--green-dark)' }}>✨ Rewards Unlocked</span>
              : <span style={{ color: 'var(--text-2)' }}>🔒 Earn {status.points_remaining} more pts</span>
            }
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-3)', fontWeight: 600, marginTop: '2px' }}>
            {status.points_earned} / {status.daily_minimum} pts today
          </div>
        </div>
      )}

      {/* Reward list */}
      <div className="card">
        <div className="section-label">Your Rewards</div>
        {rewards.length === 0 && <div style={{ textAlign: 'center', color: 'var(--text-3)', padding: '20px', fontWeight: 500 }}>No rewards yet — add one below!</div>}
        {rewards.map(r => (
          <div className="reward-card" key={r.id}>
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{r.name}</div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-3)', fontWeight: 600 }}>{r.point_cost} pts</div>
            </div>
            <button
              className={status?.gate_passed ? 'btn-success btn-sm' : 'btn-outline btn-sm'}
              disabled={!status?.gate_passed}
              onClick={() => handleRedeem(r.id)}
              style={{ opacity: status?.gate_passed ? 1 : 0.4 }}>
              {status?.gate_passed ? 'Redeem' : 'Locked'}
            </button>
          </div>
        ))}
      </div>

      {/* Add reward */}
      <div className="card">
        <div className="section-label">Add New Reward</div>
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
