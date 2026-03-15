import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

const GOALS = [
  { value: 'lose_weight', label: 'Lose Weight', icon: '⚖️' },
  { value: 'build_strength', label: 'Build Strength', icon: '💪' },
  { value: 'get_active', label: 'Get More Active', icon: '🏃' },
  { value: 'feel_better', label: 'Feel Better Overall', icon: '😊' },
]

const TTM_STAGES = [
  { value: 'precontemplation', label: "I'm not exercising and haven't thought about starting" },
  { value: 'contemplation', label: "I've been thinking about getting more active but haven't started" },
  { value: 'preparation', label: 'I do some exercise but not consistently' },
  { value: 'action', label: "I've been exercising regularly for a few months" },
  { value: 'maintenance', label: "I've been exercising regularly for 6+ months" },
]

const ACTIVITIES = [
  'Walking', 'Hiking', 'Running', 'Cycling', 'Swimming',
  'Bodyweight', 'Weights', 'Yoga', 'Martial Arts', 'Dance', 'Team Sports',
]

const EQUIPMENT = [
  { value: 'none', label: 'Nothing — bodyweight only' },
  { value: 'basic_home', label: 'Basic home equipment' },
  { value: 'full_gym', label: 'Full gym access' },
]

export default function Onboarding() {
  const [step, setStep] = useState(0)
  const [goal, setGoal] = useState('')
  const [ttm, setTtm] = useState('')
  const [age, setAge] = useState('')
  const [heightCm, setHeightCm] = useState('')
  const [weightKg, setWeightKg] = useState('')
  const [gender, setGender] = useState('')
  const [parq, setParq] = useState({ heart: false, joints: false, meds: false })
  const [motivation, setMotivation] = useState({ ext: 0, intro: 0, ident: 0, intr: 0, amot: 0 })
  const [activities, setActivities] = useState([])
  const [equipment, setEquipment] = useState('none')
  const [daysPerWeek, setDaysPerWeek] = useState(3)
  const [minsPerSession, setMinsPerSession] = useState(30)
  const [rewards, setRewards] = useState([{ name: '', cost: 100 }])
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const totalSteps = 8

  function Likert({ label, value, onChange }) {
    return (
      <div style={{ marginBottom: '16px' }}>
        <div style={{ fontSize: '0.9rem', marginBottom: '6px' }}>{label}</div>
        <div className="likert-row">
          {[1, 2, 3, 4, 5].map(n => (
            <button key={n} type="button" className={`likert-btn ${value === n ? 'selected' : ''}`} onClick={() => onChange(n)}>
              {n}
            </button>
          ))}
        </div>
        <div className="likert-labels"><span>Not at all</span><span>Very true</span></div>
      </div>
    )
  }

  async function handlePhase1() {
    setLoading(true)
    try {
      await api.savePhase1({ primary_goal: goal, ttm_stage: ttm })
      setStep(2)
    } catch (err) { alert(err.message) }
    finally { setLoading(false) }
  }

  async function handlePhase2() {
    setLoading(true)
    try {
      await api.savePhase2({
        age: age ? parseInt(age) : null,
        height_cm: heightCm ? parseFloat(heightCm) : null,
        weight_kg: weightKg ? parseFloat(weightKg) : null,
        gender: gender || null,
        parq_heart_condition: parq.heart,
        parq_joint_issues: parq.joints,
        parq_medications: parq.meds,
        motivation_external: motivation.ext || null,
        motivation_introjected: motivation.intro || null,
        motivation_identified: motivation.ident || null,
        motivation_intrinsic: motivation.intr || null,
        motivation_amotivation: motivation.amot || null,
        activity_preferences: activities.map(a => a.toLowerCase().replace(/ /g, '_')),
        equipment_access: equipment,
        days_per_week: daysPerWeek,
        minutes_per_session: minsPerSession,
      })

      // Create rewards
      for (const r of rewards) {
        if (r.name.trim()) {
          await api.createReward({ name: r.name, point_cost: r.cost || 100 })
        }
      }

      // Get recommendations
      const recs = await api.getRecommendations()
      setRecommendations(recs.recommendations || [])
      setStep(7)
    } catch (err) { alert(err.message) }
    finally { setLoading(false) }
  }

  async function handleCommit(rec) {
    try {
      const today = new Date()
      const monday = new Date(today)
      monday.setDate(today.getDate() + ((8 - today.getDay()) % 7 || 7))
      const startDate = monday.toISOString().split('T')[0]

      await api.createProgram({
        name: rec.name,
        source: rec.source,
        source_url: rec.url,
        start_date: startDate,
        duration_days: rec.duration_days || 90,
      })
      navigate('/')
    } catch (err) { alert(err.message) }
  }

  function toggleActivity(a) {
    setActivities(prev => prev.includes(a) ? prev.filter(x => x !== a) : [...prev, a])
  }

  // Progress bar
  const progress = Math.round(((step + 1) / totalSteps) * 100)

  return (
    <div className="page" style={{ paddingTop: '40px' }}>
      <div className="progress-bar" style={{ marginBottom: '24px' }}>
        <div className="progress-bar-fill" style={{ width: `${progress}%`, background: 'var(--orange)' }} />
      </div>

      {/* Step 0: Goal */}
      {step === 0 && (
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 900, letterSpacing: '-0.02em', marginBottom: '10px', fontSize: '1.4rem' }}>What matters most to you?</h2>
          <p style={{ color: 'var(--text-3)', marginBottom: '20px', fontSize: '0.9rem' }}>Pick one — you can change this anytime.</p>
          <div className="option-grid">
            {GOALS.map(g => (
              <div key={g.value} className={`option-btn ${goal === g.value ? 'selected' : ''}`} onClick={() => setGoal(g.value)}>
                <div style={{ fontSize: '1.5rem', marginBottom: '6px' }}>{g.icon}</div>
                {g.label}
              </div>
            ))}
          </div>
          <button className="btn-primary btn-full" style={{ marginTop: '20px' }} disabled={!goal} onClick={() => setStep(1)}>Continue</button>
        </div>
      )}

      {/* Step 1: TTM Stage */}
      {step === 1 && (
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 900, letterSpacing: '-0.02em', marginBottom: '10px', fontSize: '1.4rem' }}>Where are you now?</h2>
          <p style={{ color: 'var(--text-3)', marginBottom: '20px', fontSize: '0.9rem' }}>Be honest — there's no wrong answer.</p>
          {TTM_STAGES.map(s => (
            <div key={s.value}
              className={`option-btn ${ttm === s.value ? 'selected' : ''}`}
              style={{ textAlign: 'left', marginBottom: '10px' }}
              onClick={() => setTtm(s.value)}
            >{s.label}</div>
          ))}
          <button className="btn-primary btn-full" style={{ marginTop: '16px' }} disabled={!ttm || loading} onClick={handlePhase1}>
            {loading ? '...' : 'Continue'}
          </button>
        </div>
      )}

      {/* Step 2: Safety (PAR-Q+) */}
      {step === 2 && (
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 900, letterSpacing: '-0.02em', marginBottom: '10px', fontSize: '1.4rem' }}>Quick health check</h2>
          <p style={{ color: 'var(--text-3)', marginBottom: '20px', fontSize: '0.9rem' }}>For your safety — this takes 10 seconds.</p>
          {[
            { key: 'heart', label: 'I have a heart condition or high blood pressure' },
            { key: 'joints', label: 'I have bone or joint problems that could worsen with exercise' },
            { key: 'meds', label: 'I take prescription medications for a chronic condition' },
          ].map(q => (
            <label key={q.key} style={{ display: 'flex', gap: '12px', padding: '12px 0', cursor: 'pointer', borderBottom: '1px solid var(--divider)' }}>
              <input type="checkbox" checked={parq[q.key]} onChange={e => setParq({ ...parq, [q.key]: e.target.checked })} style={{ width: 'auto' }} />
              <span style={{ fontSize: '0.9rem' }}>{q.label}</span>
            </label>
          ))}
          {(parq.heart || parq.joints || parq.meds) && (
            <div style={{ marginTop: '12px', padding: '12px', background: '#FFF3E0', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem', color: '#E65100' }}>
              ⚠️ We recommend checking with your doctor before starting. This won't stop you — just be mindful.
            </div>
          )}
          <button className="btn-primary btn-full" style={{ marginTop: '20px' }} onClick={() => setStep(3)}>Continue</button>
        </div>
      )}

      {/* Step 3: Body Metrics */}
      {step === 3 && (
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 900, letterSpacing: '-0.02em', marginBottom: '10px', fontSize: '1.4rem' }}>About you</h2>
          <p style={{ color: 'var(--text-3)', marginBottom: '20px', fontSize: '0.9rem' }}>Optional — helps estimate nutrition needs.</p>
          <div className="form-group">
            <label className="form-label">Age</label>
            <input type="number" value={age} onChange={e => setAge(e.target.value)} placeholder="e.g. 35" />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div className="form-group">
              <label className="form-label">Height (cm)</label>
              <input type="number" value={heightCm} onChange={e => setHeightCm(e.target.value)} placeholder="175" />
            </div>
            <div className="form-group">
              <label className="form-label">Weight (kg)</label>
              <input type="number" value={weightKg} onChange={e => setWeightKg(e.target.value)} placeholder="80" />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Gender</label>
            <select value={gender} onChange={e => setGender(e.target.value)}>
              <option value="">Prefer not to say</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
            </select>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn-outline btn-full" onClick={() => setStep(4)}>Skip</button>
            <button className="btn-primary btn-full" onClick={() => setStep(4)}>Continue</button>
          </div>
        </div>
      )}

      {/* Step 4: Motivation (BREQ-2) */}
      {step === 4 && (
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 900, letterSpacing: '-0.02em', marginBottom: '10px', fontSize: '1.4rem' }}>What drives you?</h2>
          <p style={{ color: 'var(--text-3)', marginBottom: '20px', fontSize: '0.9rem' }}>Rate each honestly — helps us calibrate your experience.</p>
          <Likert label='"People important to me say I should exercise"' value={motivation.ext} onChange={v => setMotivation({ ...motivation, ext: v })} />
          <Likert label='"I feel bad about myself when I skip exercise"' value={motivation.intro} onChange={v => setMotivation({ ...motivation, intro: v })} />
          <Likert label='"I value what exercise does for my health"' value={motivation.ident} onChange={v => setMotivation({ ...motivation, ident: v })} />
          <Likert label='"I find exercise enjoyable and satisfying"' value={motivation.intr} onChange={v => setMotivation({ ...motivation, intr: v })} />
          <Likert label={'"I don\'t really see why I should bother"'} value={motivation.amot} onChange={v => setMotivation({ ...motivation, amot: v })} />
          <button className="btn-primary btn-full" onClick={() => setStep(5)}>Continue</button>
        </div>
      )}

      {/* Step 5: Activities + Equipment */}
      {step === 5 && (
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 900, letterSpacing: '-0.02em', marginBottom: '10px', fontSize: '1.4rem' }}>What sounds fun?</h2>
          <p style={{ color: 'var(--text-3)', marginBottom: '16px', fontSize: '0.9rem' }}>Pick all that interest you.</p>
          <div className="chip-grid" style={{ marginBottom: '24px' }}>
            {ACTIVITIES.map(a => (
              <div key={a} className={`chip ${activities.includes(a) ? 'selected' : ''}`} onClick={() => toggleActivity(a)}>{a}</div>
            ))}
          </div>
          <div className="form-group">
            <label className="form-label">Equipment access</label>
            {EQUIPMENT.map(e => (
              <div key={e.value} className={`option-btn ${equipment === e.value ? 'selected' : ''}`} style={{ textAlign: 'left', marginBottom: '8px' }} onClick={() => setEquipment(e.value)}>
                {e.label}
              </div>
            ))}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
            <div className="form-group">
              <label className="form-label">Days/week</label>
              <select value={daysPerWeek} onChange={e => setDaysPerWeek(parseInt(e.target.value))}>
                {[1, 2, 3, 4, 5, 6, 7].map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Minutes/session</label>
              <select value={minsPerSession} onChange={e => setMinsPerSession(parseInt(e.target.value))}>
                {[15, 20, 30, 45, 60, 90].map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
          </div>
          <button className="btn-primary btn-full" onClick={() => setStep(6)}>Continue</button>
        </div>
      )}

      {/* Step 6: Define Rewards */}
      {step === 6 && (
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 900, letterSpacing: '-0.02em', marginBottom: '10px', fontSize: '1.4rem' }}>Define your rewards</h2>
          <p style={{ color: 'var(--text-3)', marginBottom: '20px', fontSize: '0.9rem' }}>What guilty pleasures do you want to earn?</p>
          {rewards.map((r, i) => (
            <div key={i} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '10px', marginBottom: '12px' }}>
              <input placeholder="e.g. 1hr gaming" value={r.name} onChange={e => {
                const next = [...rewards]; next[i] = { ...r, name: e.target.value }; setRewards(next)
              }} />
              <input type="number" placeholder="100" value={r.cost} onChange={e => {
                const next = [...rewards]; next[i] = { ...r, cost: parseInt(e.target.value) || 0 }; setRewards(next)
              }} />
            </div>
          ))}
          <button className="btn-outline btn-sm" style={{ marginBottom: '20px' }} onClick={() => setRewards([...rewards, { name: '', cost: 100 }])}>
            + Add another reward
          </button>
          <button className="btn-primary btn-full" disabled={loading} onClick={handlePhase2}>
            {loading ? 'Saving...' : 'See Recommendations'}
          </button>
        </div>
      )}

      {/* Step 7: Recommendations + Commit */}
      {step === 7 && (
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 900, letterSpacing: '-0.02em', marginBottom: '10px', fontSize: '1.4rem' }}>Recommended for you</h2>
          <p style={{ color: 'var(--text-3)', marginBottom: '20px', fontSize: '0.9rem' }}>Pick a program and commit to 90 days.</p>
          {recommendations.map(rec => (
            <div className="card" key={rec.id}>
              <div style={{ fontWeight: 700, marginBottom: '4px' }}>{rec.name}</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-3)', marginBottom: '8px' }}>
                {rec.difficulty} • {rec.duration_days ? `${rec.duration_days} days` : 'Ongoing'} • {rec.source}
              </div>
              <p style={{ fontSize: '0.9rem', marginBottom: '12px' }}>{rec.description}</p>
              <div style={{ display: 'flex', gap: '8px' }}>
                <a href={rec.url} target="_blank" rel="noopener noreferrer" className="btn-outline btn-sm" style={{ display: 'inline-block' }}>View ↗</a>
                <button className="btn-primary btn-sm" onClick={() => handleCommit(rec)}>Select & Commit</button>
              </div>
            </div>
          ))}
          <button className="btn-outline btn-full" style={{ marginTop: '8px' }} onClick={() => navigate('/')}>Skip for now</button>
        </div>
      )}
    </div>
  )
}
