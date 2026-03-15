import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

/* === Tooltip Component === */
function Tip({ text, children }) {
  const [show, setShow] = useState(false)
  return (
    <span style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}>
      {children}
      <span
        onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}
        onClick={(e) => { e.stopPropagation(); setShow(s => !s) }}
        style={{
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          width: '18px', height: '18px', borderRadius: '50%', marginLeft: '6px',
          background: 'rgba(0,0,0,0.06)', color: 'var(--text-3)', cursor: 'help',
          fontSize: '0.7rem', fontWeight: 800, flexShrink: 0,
        }}>?</span>
      {show && (
        <span style={{
          position: 'absolute', bottom: 'calc(100% + 8px)', left: '50%', transform: 'translateX(-50%)',
          background: 'var(--text)', color: '#fff', padding: '10px 14px', borderRadius: 'var(--r-sm)',
          fontSize: '0.78rem', lineHeight: 1.45, fontWeight: 500, width: '240px',
          boxShadow: 'var(--shadow-3)', zIndex: 50, pointerEvents: 'none',
        }}>{text}</span>
      )}
    </span>
  )
}

const GOALS = [
  { value: 'lose_weight', label: 'Lose Weight', icon: '⚖️', tip: 'Focus on caloric deficit through cardio and portion-controlled nutrition.' },
  { value: 'build_strength', label: 'Build Strength', icon: '💪', tip: 'Progressive overload training — gradually increasing weight or resistance.' },
  { value: 'get_active', label: 'Get More Active', icon: '🏃', tip: 'Building a consistent movement habit. Walking counts!' },
  { value: 'feel_better', label: 'Feel Better Overall', icon: '😊', tip: 'Mind-body balance — stress relief, sleep quality, energy levels.' },
]

const TTM_STAGES = [
  { value: 'precontemplation', label: "I'm not exercising and haven't thought about starting", tip: 'Pre-contemplation: No intention to act. We\'ll start with awareness and gentle nudges.' },
  { value: 'contemplation', label: "I've been thinking about getting more active but haven't started", tip: 'Contemplation: Weighing pros and cons. We\'ll help tip the balance toward action.' },
  { value: 'preparation', label: 'I do some exercise but not consistently', tip: 'Preparation: Ready to commit. We\'ll help you build a sustainable routine.' },
  { value: 'action', label: "I've been exercising regularly for a few months", tip: 'Action: Building the habit. We\'ll help you stay consistent and avoid burnout.' },
  { value: 'maintenance', label: "I've been exercising regularly for 6+ months", tip: 'Maintenance: Solid habit. We\'ll help you progress and keep things interesting.' },
]

const ACTIVITIES = [
  'Walking', 'Hiking', 'Running', 'Cycling', 'Swimming',
  'Bodyweight', 'Weights', 'Yoga', 'Martial Arts', 'Dance', 'Team Sports',
  'Pilates', 'Rowing', 'Jump Rope', 'Stretching',
]

const EQUIPMENT_OPTIONS = [
  { value: 'bicycle', label: '🚲 Bicycle' },
  { value: 'pool', label: '🏊 Pool' },
  { value: 'free_weights', label: '🏋️ Free Weights' },
  { value: 'squat_rack', label: '🦵 Squat Rack' },
  { value: 'bench_press', label: '💺 Bench Press' },
  { value: 'machines', label: '⚙️ Machines' },
  { value: 'resistance_bands', label: '🔗 Resistance Bands' },
  { value: 'pull_up_bar', label: '🔩 Pull-up Bar' },
  { value: 'kettlebell', label: '🔔 Kettlebell' },
  { value: 'jump_rope', label: '⏩ Jump Rope' },
  { value: 'yoga_mat', label: '🧘 Yoga Mat' },
  { value: 'treadmill', label: '🏃 Treadmill' },
  { value: 'stationary_bike', label: '🚴 Stationary Bike' },
  { value: 'rowing_machine', label: '🚣 Rowing Machine' },
]

const BREQ2_ITEMS = [
  { key: 'ext', label: '"People important to me say I should exercise"', tip: 'External regulation: exercising because others push you to. Least self-determined motivation.' },
  { key: 'intro', label: '"I feel bad about myself when I skip exercise"', tip: 'Introjected regulation: guilt or obligation as a driver. Better than external, but still fragile.' },
  { key: 'ident', label: '"I value what exercise does for my health"', tip: 'Identified regulation: you see exercise as personally important. A strong, durable motivator.' },
  { key: 'intr', label: '"I find exercise enjoyable and satisfying"', tip: 'Intrinsic motivation: you exercise because it\'s fun. The most sustainable form of motivation.' },
  { key: 'amot', label: '"I don\'t really see why I should bother"', tip: 'Amotivation: no perceived reason to exercise. If this is high, we\'ll start with very small wins.' },
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
  const [equipmentList, setEquipmentList] = useState([])
  const [daysPerWeek, setDaysPerWeek] = useState(3)
  const [minsPerSession, setMinsPerSession] = useState(30)
  const [rewards, setRewards] = useState([{ name: '', cost: 100 }])
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const totalSteps = 8

  function Likert({ label, value, onChange, tip }) {
    return (
      <div style={{ marginBottom: '16px' }}>
        <div style={{ fontSize: '0.9rem', marginBottom: '6px' }}>
          {tip ? <Tip text={tip}>{label}</Tip> : label}
        </div>
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
      // Derive legacy equipment_access from equipment list
      let equipAccess = 'none'
      const gym = ['squat_rack', 'bench_press', 'machines']
      const basic = ['free_weights', 'resistance_bands', 'pull_up_bar', 'kettlebell', 'yoga_mat', 'jump_rope']
      if (equipmentList.some(e => gym.includes(e))) equipAccess = 'full_gym'
      else if (equipmentList.some(e => basic.includes(e))) equipAccess = 'basic_home'

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
        equipment_access: equipAccess,
        equipment_list: equipmentList,
        days_per_week: daysPerWeek,
        minutes_per_session: minsPerSession,
      })

      for (const r of rewards) {
        if (r.name.trim()) {
          await api.createReward({ name: r.name, point_cost: r.cost || 100 })
        }
      }

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

  function toggleEquipment(val) {
    setEquipmentList(prev => prev.includes(val) ? prev.filter(x => x !== val) : [...prev, val])
  }

  const progress = Math.round(((step + 1) / totalSteps) * 100)
  const h2Style = { fontFamily: 'var(--font-display)', fontWeight: 900, letterSpacing: '-0.02em', marginBottom: '10px', fontSize: '1.4rem' }

  return (
    <div className="page" style={{ paddingTop: '40px' }}>
      <div className="progress-bar" style={{ marginBottom: '24px' }}>
        <div className="progress-bar-fill" style={{ width: `${progress}%`, background: 'var(--orange)' }} />
      </div>

      {/* Step 0: Goal */}
      {step === 0 && (
        <div>
          <h2 style={h2Style}>
            <Tip text="Your primary goal shapes which programs we recommend, how we structure your points, and what success looks like for you.">
              What matters most to you?
            </Tip>
          </h2>
          <p style={{ color: 'var(--text-3)', marginBottom: '20px', fontSize: '0.9rem' }}>Pick one — you can change this anytime.</p>
          <div className="option-grid">
            {GOALS.map(g => (
              <div key={g.value} className={`option-btn ${goal === g.value ? 'selected' : ''}`} onClick={() => setGoal(g.value)}>
                <div style={{ fontSize: '1.5rem', marginBottom: '6px' }}>{g.icon}</div>
                <Tip text={g.tip}>{g.label}</Tip>
              </div>
            ))}
          </div>
          <button className="btn-primary btn-full" style={{ marginTop: '20px' }} disabled={!goal} onClick={() => setStep(1)}>Continue</button>
        </div>
      )}

      {/* Step 1: TTM Stage */}
      {step === 1 && (
        <div>
          <h2 style={h2Style}>
            <Tip text="Based on the Transtheoretical Model (Stages of Change). This helps us match you with the right intensity — pushing too hard too early is the #1 reason people quit.">
              Where are you now?
            </Tip>
          </h2>
          <p style={{ color: 'var(--text-3)', marginBottom: '20px', fontSize: '0.9rem' }}>Be honest — there's no wrong answer.</p>
          {TTM_STAGES.map(s => (
            <div key={s.value}
              className={`option-btn ${ttm === s.value ? 'selected' : ''}`}
              style={{ textAlign: 'left', marginBottom: '10px' }}
              onClick={() => setTtm(s.value)}
            >
              <Tip text={s.tip}>{s.label}</Tip>
            </div>
          ))}
          <button className="btn-primary btn-full" style={{ marginTop: '16px' }} disabled={!ttm || loading} onClick={handlePhase1}>
            {loading ? '...' : 'Continue'}
          </button>
        </div>
      )}

      {/* Step 2: Safety (PAR-Q+) */}
      {step === 2 && (
        <div>
          <h2 style={h2Style}>
            <Tip text="Based on the PAR-Q+ (Physical Activity Readiness Questionnaire). A standard pre-exercise safety screening used by fitness professionals worldwide.">
              Quick health check
            </Tip>
          </h2>
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
            <div style={{ marginTop: '12px', padding: '12px', background: '#FFF3E0', borderRadius: 'var(--r-sm)', fontSize: '0.85rem', color: '#E65100' }}>
              ⚠️ We recommend checking with your doctor before starting. This won't stop you — just be mindful.
            </div>
          )}
          <button className="btn-primary btn-full" style={{ marginTop: '20px' }} onClick={() => setStep(3)}>Continue</button>
        </div>
      )}

      {/* Step 3: Body Metrics */}
      {step === 3 && (
        <div>
          <h2 style={h2Style}>About you</h2>
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
          <h2 style={h2Style}>
            <Tip text="Based on BREQ-2 (Behavioural Regulation in Exercise Questionnaire). Measures your motivation type from external pressure to intrinsic enjoyment. Your Relative Autonomy Index (RAI) score helps us calibrate how much we push vs. encourage.">
              What drives you?
            </Tip>
          </h2>
          <p style={{ color: 'var(--text-3)', marginBottom: '20px', fontSize: '0.9rem' }}>Rate each honestly — helps us calibrate your experience.</p>
          {BREQ2_ITEMS.map(item => (
            <Likert
              key={item.key}
              label={item.label}
              tip={item.tip}
              value={motivation[item.key]}
              onChange={v => setMotivation({ ...motivation, [item.key]: v })}
            />
          ))}
          <button className="btn-primary btn-full" onClick={() => setStep(5)}>Continue</button>
        </div>
      )}

      {/* Step 5: Activities + Equipment */}
      {step === 5 && (
        <div>
          <h2 style={h2Style}>What sounds fun?</h2>
          <p style={{ color: 'var(--text-3)', marginBottom: '16px', fontSize: '0.9rem' }}>Pick all that interest you.</p>
          <div className="chip-grid" style={{ marginBottom: '24px' }}>
            {ACTIVITIES.map(a => (
              <div key={a} className={`chip ${activities.includes(a) ? 'selected' : ''}`} onClick={() => toggleActivity(a)}>{a}</div>
            ))}
          </div>

          <div className="form-group">
            <label className="form-label">
              <Tip text="Select everything you have access to. This helps us recommend programs that match your available equipment — no point suggesting barbell work if you don't have a rack.">
                Equipment you have access to
              </Tip>
            </label>
            <div className="chip-grid">
              {EQUIPMENT_OPTIONS.map(e => (
                <div key={e.value} className={`chip ${equipmentList.includes(e.value) ? 'selected' : ''}`}
                  onClick={() => toggleEquipment(e.value)}>
                  {e.label}
                </div>
              ))}
            </div>
            {equipmentList.length === 0 && (
              <p style={{ color: 'var(--text-3)', fontSize: '0.8rem', marginTop: '8px', fontStyle: 'italic' }}>
                No selection = bodyweight only. That's perfectly fine!
              </p>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '16px', marginBottom: '16px' }}>
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
          <h2 style={h2Style}>
            <Tip text="The reward gate is the core mechanic: you can't access your rewards until you hit your daily point minimum. This creates a behavioral contract — earn first, enjoy second.">
              Define your rewards
            </Tip>
          </h2>
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
          <h2 style={h2Style}>Recommended for you</h2>
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
