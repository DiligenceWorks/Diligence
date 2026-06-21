import { useState, useEffect } from 'react'
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

export default function SettingsIntegrations() {
  const [providers, setProviders] = useState({})
  const [status, setStatus] = useState({})
  const [loading, setLoading] = useState(true)
  const [configuring, setConfiguring] = useState(null)  // provider key being configured
  const [formData, setFormData] = useState({})
  const [saving, setSaving] = useState(false)

  useEffect(() => { loadAll() }, [])

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

  return (
    <div className="page" style={{ maxWidth: 700, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 24 }}>Integrations</h1>
      <p style={{ color: 'var(--text-2)', marginBottom: 24, fontSize: '0.9rem' }}>
        Configure your fitness devices and services. Credentials are encrypted and stored locally — never sent to any external server.
      </p>

      {Object.entries(providers).map(([key, info]) => (
        <div key={key} style={{
          background: 'var(--surface-2)', borderRadius: 'var(--r-md)', padding: 20, marginBottom: 12,
          border: status[key] === 'connected' ? '2px solid var(--accent)' : '1px solid var(--border)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <strong style={{ fontSize: '1rem' }}>{info.name}</strong>
            <span style={{
              fontSize: '0.75rem', padding: '3px 10px', borderRadius: 20, fontWeight: 600,
              background: STATUS_COLORS[status[key] || 'not_configured'] + '22',
              color: STATUS_COLORS[status[key] || 'not_configured'],
            }}>
              {STATUS_LABELS[status[key] || 'not_configured']}
            </span>
          </div>

          <p style={{ color: 'var(--text-2)', fontSize: '0.85rem', margin: '0 0 12px' }}>
            {info.help_text}
          </p>

          {info.help_url && (
            <a href={info.help_url} target="_blank" rel="noopener noreferrer"
              style={{ fontSize: '0.8rem', color: 'var(--accent)' }}>
              Developer portal →
            </a>
          )}

          {configuring === key ? (
            <div style={{ marginTop: 12, padding: 16, background: 'var(--surface)', borderRadius: 'var(--r-sm)' }}>
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
                      border: '1px solid var(--border)', fontSize: '0.9rem', boxSizing: 'border-box',
                    }}
                    placeholder={`Enter ${field.replace(/_/g, ' ')}`}
                  />
                </div>
              ))}
              <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                <button onClick={() => handleSave(key)} disabled={saving}
                  style={{
                    background: 'var(--accent)', color: '#fff', border: 'none',
                    padding: '8px 20px', borderRadius: 'var(--r-sm)', cursor: 'pointer', fontWeight: 600,
                  }}>
                  {saving ? 'Saving...' : 'Save'}
                </button>
                <button onClick={() => setConfiguring(null)}
                  style={{
                    background: 'transparent', color: 'var(--text-2)', border: '1px solid var(--border)',
                    padding: '8px 20px', borderRadius: 'var(--r-sm)', cursor: 'pointer',
                  }}>
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button onClick={() => startConfigure(key)}
              style={{
                marginTop: 8, background: 'transparent', color: 'var(--accent)',
                border: '1px solid var(--accent)', padding: '6px 16px', borderRadius: 'var(--r-sm)',
                cursor: 'pointer', fontSize: '0.85rem', fontWeight: 600,
              }}>
              {status[key] === 'not_configured' ? 'Configure' : 'Reconfigure'}
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
