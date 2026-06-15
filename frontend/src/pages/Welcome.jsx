import { useNavigate } from 'react-router-dom'

export default function Welcome() {
  const navigate = useNavigate()

  return (
    <div className="page" style={{ maxWidth: 600, margin: '0 auto', padding: '40px 20px', textAlign: 'center' }}>
      <div style={{ fontSize: '3rem', marginBottom: 16 }}>💪</div>
      <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: 8 }}>Earn Before You Spend</h1>
      <p style={{ color: 'var(--text-2)', fontSize: '1rem', lineHeight: 1.6, marginBottom: 32 }}>
        This app runs on a simple idea: you earn points by doing healthy things
        (workouts, logging meals, hitting step goals), and you spend points on
        guilty pleasures you configure yourself.
      </p>

      <div style={{ background: 'var(--surface-2)', borderRadius: 'var(--r-md)', padding: 24, marginBottom: 24, textAlign: 'left' }}>
        <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
          <span style={{ fontSize: '1.5rem' }}>🔒</span>
          <div>
            <strong>Daily Gate</strong>
            <p style={{ color: 'var(--text-2)', margin: '4px 0 0', fontSize: '0.9rem' }}>
              Until you earn enough points today, your rewards stay locked. Hit your target, and the gate opens.
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
          <span style={{ fontSize: '1.5rem' }}>🎮</span>
          <div>
            <strong>Your Rules</strong>
            <p style={{ color: 'var(--text-2)', margin: '4px 0 0', fontSize: '0.9rem' }}>
              You set the rewards — gaming time, takeout, screen time, whatever you want. You hold yourself accountable.
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 16 }}>
          <span style={{ fontSize: '1.5rem' }}>🤖</span>
          <div>
            <strong>AI Agent (Optional)</strong>
            <p style={{ color: 'var(--text-2)', margin: '4px 0 0', fontSize: '0.9rem' }}>
              Connect an AI agent to log activities by voice, get nudged when you're behind, and have a fitness companion that knows your goals.
            </p>
          </div>
        </div>
      </div>

      <button
        onClick={() => navigate('/register')}
        style={{
          background: 'var(--accent)', color: '#fff', border: 'none', borderRadius: 'var(--r-sm)',
          padding: '14px 32px', fontSize: '1rem', fontWeight: 600, cursor: 'pointer', width: '100%',
        }}
      >
        Get Started
      </button>

      <p style={{ color: 'var(--text-3)', fontSize: '0.8rem', marginTop: 16 }}>
        Points reset weekly. Each week is a fresh start.
      </p>
    </div>
  )
}
