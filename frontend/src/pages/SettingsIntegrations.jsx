import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { api } from '../api'

const STATUS_COLORS = {
  connected: 'var(--green)',
  configured: 'var(--amber)',
  not_configured: 'var(--text-3)',
}

const STATUS_LABELS = {
  connected: 'Connected',
  configured: 'Configured',
  not_configured: 'Not configured',
}

const CATEGORY_ORDER = ['device', 'ai_provider', 'nutrition', 'notifications']

const CATEGORY_INFO = {
  device: {
    title: 'Fitness Devices',
    description: 'Sync workouts automatically from your watch or tracker.',
  },
  ai_provider: {
    title: 'AI Coaching',
    description: 'Connect an LLM to power the built-in AI coach in the Coach tab. One provider is enough.',
  },
  nutrition: {
    title: 'Nutrition',
    description: 'Food databases for accurate macro tracking.',
  },
  notifications: {
    title: 'Notifications',
    description: 'Get alerts when things happen.',
  },
}

const SYNC_BADGE = {
  coming_soon: { label: 'Coming soon', color: 'var(--text-3)' },
  mcp_bridge: { label: 'MCP bridge', color: 'var(--accent)' },
}

export default function SettingsIntegrations() {
  const [providers, setProviders] = useState({})
  const [status, setStatus] = useState({})
  const [loading, setLoading] = useState(true)
  const [configuring, setConfiguring] = useState(null)
  const [formData, setFormData] = useState({})
  const [saving, setSaving] = useState(false)
  const location = useLocation()

  useEffect(() => { loadAll() }, [])

  // Handle hash scrolling (e.g. /settings/integrations#ai-coaching)
  useEffect(() => {
    if (!loading && location.hash) {
      const el = document.getElementById(location.hash.slice(1))
      if (el) setTimeout(() => el.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100)
    }
  }, [loading, location.hash])

  async function loadAll() {
    try {
      const [p, s] = await Promise.all([api.listProviders(), api.fullIntegrationStatus()])
      setProviders(p)
      setStatus(s)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  function startConfigure(key) {
    setConfiguring(key)
    const fields = providers[key]?.fields || []
    setFormData(Object.fromEntries(fields.map(f => [f, ''])))
  }

  async function handleSave(key) {
    setSaving(true)
    try {
      await api.configureIntegration(key, formData)
      setConfiguring(null)
      await loadAll()
    } catch (err) { alert(`Failed: ${err.message}`) }
    finally { setSaving(false) }
  }

  if (loading) return <div className="page"><div className="loading">Loading...</div></div>

  // Group providers by category
  const grouped = {}
  for (const [key, info] of Object.entries(providers)) {
    const cat = info.category || 'other'
    if (!grouped[cat]) grouped[cat] = []
    grouped[cat].push({ key, ...info })
  }

  return (
    <div className="page" style={{ maxWidth: 700, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 8 }}>Integrations</h1>
      <p style={{ color: 'var(--text-2)', marginBottom: 24, fontSize: '0.9rem' }}>
        Configure your fitness devices and services. Credentials are encrypted and stored locally — never sent to any external server.
      </p>

      {CATEGORY_ORDER.map(cat => {
        const items = grouped[cat]
        if (!items || items.length === 0) return null
        const catInfo = CATEGORY_INFO[cat] || { title: cat, description: '' }
        const sectionId = catInfo.title.toLowerCase().replace(/\s+/g, '-')

        return (
          <div key={cat} id={sectionId} style={{ marginBottom: 32 }}>
            <div style={{
              fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase',
              letterSpacing: '0.08em', color: 'var(--accent)',
              fontFamily: 'var(--font-mono)', marginBottom: 4,
            }}>
              {catInfo.title}
            </div>
            <p style={{ color: 'var(--text-3)', fontSize: '0.82rem', marginBottom: 12 }}>
              {catInfo.description}
              {cat === 'ai_provider' && (
                <span> <a href="/agent" style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: 600 }}>
                  Or connect Claude Desktop / Cursor via MCP →
                </a></span>
              )}
            </p>

            {items.map(info => {
              const { key } = info
              const badge = SYNC_BADGE[info.sync_status]
              const isMcpBridge = info.sync_status === 'mcp_bridge'
              const isComingSoon = info.sync_status === 'coming_soon'

              return (
                <div key={key} style={{
                  background: 'var(--card)', borderRadius: 'var(--r)', padding: 20, marginBottom: 10,
                  border: status[key] === 'connected' ? '2px solid var(--accent)' : '1px solid var(--card-border)',
                  opacity: isComingSoon ? 0.7 : 1,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <strong style={{ fontSize: '1rem' }}>{info.name}</strong>
                      {badge && (
                        <span style={{
                          fontSize: '0.65rem', padding: '2px 8px', borderRadius: 20,
                          fontWeight: 600, fontFamily: 'var(--font-mono)',
                          background: badge.color + '18', color: badge.color,
                        }}>
                          {badge.label}
                        </span>
                      )}
                    </div>
                    <span style={{
                      fontSize: '0.75rem', padding: '3px 10px', borderRadius: 20, fontWeight: 600,
                      background: STATUS_COLORS[status[key] || 'not_configured'] + '22',
                      color: STATUS_COLORS[status[key] || 'not_configured'],
                    }}>
                      {STATUS_LABELS[status[key] || 'not_configured']}
                    </span>
                  </div>

                  <p style={{ color: 'var(--text-2)', fontSize: '0.85rem', margin: '0 0 8px' }}>
                    {info.help_text}
                  </p>

                  {info.warning && (
                    <p style={{
                      fontSize: '0.78rem', color: 'var(--amber)', margin: '0 0 8px',
                      padding: '6px 10px', background: 'var(--amber-bg)', borderRadius: 'var(--r-sm)',
                    }}>
                      ⚠ {info.warning}
                    </p>
                  )}

                  {info.help_url && (
                    <a href={info.help_url} target="_blank" rel="noopener noreferrer"
                      style={{ fontSize: '0.8rem', color: 'var(--accent)' }}>
                      {isMcpBridge ? 'MCP setup docs →' : 'Developer portal →'}
                    </a>
                  )}

                  {/* Configuration form — skip for mcp_bridge and coming_soon */}
                  {!isMcpBridge && !isComingSoon && configuring === key ? (
                    <div style={{ marginTop: 12, padding: 16, background: 'var(--bg)', borderRadius: 'var(--r-sm)' }}>
                      {info.fields.map(field => (
                        <div key={field} style={{ marginBottom: 10 }}>
                          <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: 4 }}>
                            {field.replace(/_/g, ' ')}
                          </label>
                          <input
                            type={field.includes('secret') || field.includes('token') || field.includes('key') ? 'password' : 'text'}
                            value={formData[field] || ''}
                            onChange={e => setFormData({ ...formData, [field]: e.target.value })}
                            style={{
                              width: '100%', padding: '8px 12px', borderRadius: 'var(--r-sm)',
                              border: '1px solid var(--card-border)', fontSize: '0.9rem', boxSizing: 'border-box',
                            }}
                            placeholder={`Enter ${field.replace(/_/g, ' ')}`}
                          />
                        </div>
                      ))}
                      <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                        <button onClick={() => handleSave(key)} disabled={saving}
                          style={{
                            background: 'var(--accent)', color: 'var(--text-inv)', border: 'none',
                            padding: '8px 20px', borderRadius: 'var(--r-sm)', cursor: 'pointer', fontWeight: 600,
                          }}>
                          {saving ? 'Saving...' : 'Save'}
                        </button>
                        <button onClick={() => setConfiguring(null)}
                          style={{
                            background: 'transparent', color: 'var(--text-2)', border: '1px solid var(--card-border)',
                            padding: '8px 20px', borderRadius: 'var(--r-sm)', cursor: 'pointer',
                          }}>
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : !isMcpBridge && !isComingSoon ? (
                    <button onClick={() => startConfigure(key)}
                      style={{
                        marginTop: 8, background: 'transparent', color: 'var(--accent)',
                        border: '1px solid var(--accent)', padding: '6px 16px', borderRadius: 'var(--r-sm)',
                        cursor: 'pointer', fontSize: '0.85rem', fontWeight: 600,
                      }}>
                      {status[key] === 'not_configured' || !status[key] ? 'Configure' : 'Reconfigure'}
                    </button>
                  ) : null}
                </div>
              )
            })}
          </div>
        )
      })}
    </div>
  )
}
