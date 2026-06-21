import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

const FAST_PRESETS = [
  { label: '16:8 Daily', hours: 16, type: 'daily' },
  { label: '18:6', hours: 18, type: 'daily' },
  { label: '20:4', hours: 20, type: 'daily' },
  { label: '24h Weekly', hours: 24, type: 'weekly_24' },
  { label: '48h', hours: 48, type: 'long_48' },
  { label: '72h Kickoff', hours: 72, type: 'long_72' },
]

function MacroBar({ label, value, target, unit, color, inverse }) {
  const pct = target > 0 ? Math.min(100, Math.round((value / target) * 100)) : 0
  const ok = inverse ? value <= target : value >= target * 0.85
  return (
    <div style={{ marginBottom: '14px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.85rem' }}>
        <span style={{ fontWeight: 700 }}>{label}</span>
        <span style={{ color: ok ? 'var(--green-dark)' : 'var(--text-3)', fontWeight: 600 }}>
          {Math.round(value)}{inverse ? '' : ` / ${target}`} {unit}
          {inverse && ` / ${target} cap`}
        </span>
      </div>
      <div className="progress-bar" style={{ height: '8px' }}>
        <div className="progress-bar-fill" style={{
          width: `${pct}%`,
          background: inverse
            ? (value <= target ? 'var(--green)' : 'var(--red)')
            : color,
        }} />
      </div>
    </div>
  )
}

function FastTimer({ fast }) {
  const [, tick] = useState(0)
  useEffect(() => {
    const i = setInterval(() => tick(t => t + 1), 60000)
    return () => clearInterval(i)
  }, [])

  const elapsed = (new Date() - new Date(fast.started_at)) / 1000 / 3600
  const pct = Math.min(100, (elapsed / fast.target_hours) * 100)
  const hit = elapsed >= fast.target_hours
  const hrs = Math.floor(elapsed)
  const mins = Math.floor((elapsed - hrs) * 60)

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
        <span style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '1.6rem' }}>
          {hrs}h {mins}m
        </span>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-3)', fontWeight: 600 }}>
          / {fast.target_hours}h target
        </span>
      </div>
      <div className="progress-bar" style={{ height: '12px' }}>
        <div className="progress-bar-fill" style={{
          width: `${pct}%`,
          background: hit
            ? 'linear-gradient(90deg, #00C853, #69F0AE)'
            : 'linear-gradient(90deg, #7C4DFF, #B388FF)',
        }} />
      </div>
      {hit && (
        <div style={{ marginTop: '8px', fontSize: '0.9rem', color: 'var(--green-dark)', fontWeight: 700 }}>
          ✓ Target reached — you can end now or push further
        </div>
      )}
    </div>
  )
}

export default function Nutrition() {
  const [data, setData] = useState(null)
  const [electrolytes, setElectrolytes] = useState(null)
  const [loading, setLoading] = useState(true)
  const [fastPreset, setFastPreset] = useState(FAST_PRESETS[0])
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()

  useEffect(() => { load() }, [])
  async function load() {
    try {
      const [d, e] = await Promise.all([
        api.nutritionToday(),
        api.getElectrolytesToday(),
      ])
      setData(d)
      setElectrolytes(e)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  async function handleStartFast() {
    setBusy(true)
    try {
      await api.startFast({ target_hours: fastPreset.hours, fast_type: fastPreset.type })
      await load()
    } catch (err) { alert(err.message) }
    finally { setBusy(false) }
  }

  async function handleEndFast() {
    if (!confirm('End this fast now?')) return
    setBusy(true)
    try {
      const result = await api.endFast(data.active_fast.id)
      alert(`Fast ended. +${result.points_awarded} pts earned.`)
      await load()
    } catch (err) { alert(err.message) }
    finally { setBusy(false) }
  }

  async function quickElectrolyte(type) {
    // Quick-add preset doses
    const doses = {
      morning: { sodium_mg: 2300, potassium_mg: 800, magnesium_mg: 0, notes: 'Morning drink' },
      midday:  { sodium_mg: 2300, potassium_mg: 800, magnesium_mg: 0, notes: 'Midday drink' },
      mag_pm:  { sodium_mg: 0, potassium_mg: 0, magnesium_mg: 400, notes: 'Magnesium glycinate PM' },
    }
    try {
      await api.logElectrolytes(doses[type])
      await load()
    } catch (err) { alert(err.message) }
  }

  if (loading) return <div className="page"><div className="loading">Loading...</div></div>
  if (!data) return <div className="page"><div className="error-msg">Failed to load</div></div>

  const m = data.macros
  const t = data.targets
  const c = data.compliance
  const w = data.eating_window

  return (
    <div className="page">
      <h1 className="page-title">Nutrition</h1>

      {/* === Compliance banner === */}
      <div className={`gate-banner ${c.compliant_day ? 'gate-earned' : 'gate-locked'}`}>
        <div className="section-label" style={{ marginBottom: '4px' }}>Today's Keto Day</div>
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '1.4rem',
          color: c.compliant_day ? 'var(--green)' : 'var(--accent)' }}>
          {c.compliant_day ? '✓ Compliant' : '⏳ In progress'}
        </div>
        <div style={{ fontSize: '0.82rem', color: 'var(--text-2)', marginTop: '6px' }}>
          {c.carb_ok ? '✓' : '✗'} Net carbs under cap &nbsp;·&nbsp;
          {c.protein_ok ? '✓' : '✗'} Protein target
        </div>
      </div>

      {/* === Active fast or start fast === */}
      <div className="card">
        <div className="section-label">Fasting</div>
        {data.active_fast ? (
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-3)', marginBottom: '8px' }}>
              {data.active_fast.fast_type.replace('_', ' ')} fast in progress
            </div>
            <FastTimer fast={data.active_fast} />
            <button className="btn-outline btn-full" onClick={handleEndFast} disabled={busy}
              style={{ marginTop: '14px' }}>
              End Fast
            </button>
          </div>
        ) : (
          <div>
            <div style={{ marginBottom: '10px', fontSize: '0.85rem', color: 'var(--text-2)' }}>
              Eating window: <strong>{w.display}</strong>
              {w.in_window_now
                ? <span style={{ color: 'var(--green-dark)', marginLeft: '8px' }}>● open</span>
                : <span style={{ color: 'var(--text-3)', marginLeft: '8px' }}>○ closed</span>}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', marginBottom: '12px' }}>
              {FAST_PRESETS.map(p => (
                <button key={p.hours}
                  className={fastPreset.hours === p.hours ? 'btn-primary btn-sm' : 'btn-outline btn-sm'}
                  onClick={() => setFastPreset(p)}>
                  {p.label}
                </button>
              ))}
            </div>
            <button className="btn-primary btn-full" onClick={handleStartFast} disabled={busy}>
              Start {fastPreset.label} Fast
            </button>
          </div>
        )}
      </div>

      {/* === Macro rings === */}
      <div className="card">
        <div className="section-label">Today's Macros</div>
        <MacroBar label="Net carbs" value={m.net_carbs_g} target={t.net_carbs_cap} unit="g" inverse />
        <MacroBar label="Protein" value={m.protein_g} target={t.protein_g} unit="g" color="var(--accent)" />
        <MacroBar label="Fat" value={m.fat_g} target={t.fat_g} unit="g" color="#FFA726" />
        <MacroBar label="Calories" value={m.calories} target={t.calories} unit="kcal" color="#2979FF" />
        <button className="btn-outline btn-full btn-sm" onClick={() => navigate('/food')}
          style={{ marginTop: '8px' }}>
          + Log Food
        </button>
      </div>

      {/* === Electrolytes === */}
      {electrolytes && (
        <div className="card">
          <div className="section-label">Electrolytes Today</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '12px' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-3)', fontWeight: 700 }}>SODIUM</div>
              <div style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '1.1rem' }}>
                {electrolytes.sodium_mg}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-3)' }}>/ {electrolytes.targets.sodium_mg}mg</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-3)', fontWeight: 700 }}>POTASSIUM</div>
              <div style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '1.1rem' }}>
                {electrolytes.potassium_mg}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-3)' }}>/ {electrolytes.targets.potassium_mg}mg</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-3)', fontWeight: 700 }}>MAGNESIUM</div>
              <div style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '1.1rem' }}>
                {electrolytes.magnesium_mg}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-3)' }}>/ {electrolytes.targets.magnesium_mg}mg</div>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
            <button className="btn-outline btn-sm" onClick={() => quickElectrolyte('morning')}>+ Morning</button>
            <button className="btn-outline btn-sm" onClick={() => quickElectrolyte('midday')}>+ Midday</button>
            <button className="btn-outline btn-sm" onClick={() => quickElectrolyte('mag_pm')}>+ Mag PM</button>
          </div>
        </div>
      )}
    </div>
  )
}
