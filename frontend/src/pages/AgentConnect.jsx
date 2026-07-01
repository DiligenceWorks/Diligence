import { useState, useEffect } from 'react'
import { api } from '../api'

function CopyButton({ text, label }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch { /* fallback for non-HTTPS */ }
  }
  return (
    <button
      onClick={handleCopy}
      className="btn-outline btn-sm"
      style={{ fontSize: '0.75rem', padding: '6px 12px', whiteSpace: 'nowrap' }}
    >
      {copied ? 'Copied' : (label || 'Copy')}
    </button>
  )
}

function CodeBlock({ children, copyText }) {
  return (
    <div style={{
      background: 'var(--bg)', border: '1px solid var(--divider)',
      borderRadius: 'var(--r-sm)', padding: '14px 16px',
      fontFamily: 'var(--font-mono)', fontSize: '0.78rem', lineHeight: 1.6,
      overflowX: 'auto', position: 'relative', whiteSpace: 'pre',
    }}>
      {copyText && (
        <div style={{ position: 'absolute', top: '8px', right: '8px' }}>
          <CopyButton text={copyText} />
        </div>
      )}
      {children}
    </div>
  )
}

export default function AgentConnect() {
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showToken, setShowToken] = useState(false)

  useEffect(() => {
    api.agentConfig()
      .then(setConfig)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="page"><div className="loading">Loading...</div></div>
  if (!config) return <div className="page"><div className="error-msg">Failed to load agent config</div></div>

  const maskedToken = config.api_token
    ? config.api_token.slice(0, 8) + '\u2026' + config.api_token.slice(-4)
    : null

  const claudeDesktopConfig = JSON.stringify({
    "mcpServers": {
      "diligence": {
        "url": config.mcp_url,
        ...(config.api_token ? { "headers": { "Authorization": `Bearer ${config.api_token}` } } : {})
      }
    }
  }, null, 2)

  return (
    <div className="page">
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{
          fontFamily: 'var(--font-display)', fontWeight: 800,
          fontSize: '1.3rem', marginBottom: '4px',
        }}>
          Connect Your AI Agent
        </h1>
        <p style={{ color: 'var(--text-3)', fontSize: '0.85rem' }}>
          Use any MCP-compatible AI to log workouts, track food, and manage your fitness.
        </p>
      </div>

      {/* Connection Details */}
      <div className="card">
        <div className="section-label">Connection</div>

        <div style={{ marginBottom: '14px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-3)', fontWeight: 600, marginBottom: '4px' }}>
            MCP Endpoint
          </div>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            background: 'var(--bg)', borderRadius: 'var(--r-sm)',
            padding: '10px 12px', border: '1px solid var(--divider)',
          }}>
            <code style={{
              flex: 1, fontFamily: 'var(--font-mono)', fontSize: '0.82rem',
              color: 'var(--accent)', wordBreak: 'break-all',
            }}>
              {config.mcp_url}
            </code>
            <CopyButton text={config.mcp_url} />
          </div>
        </div>

        {config.api_token && (
          <div style={{ marginBottom: '14px' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-3)', fontWeight: 600, marginBottom: '4px' }}>
              API Token
            </div>
            <div style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              background: 'var(--bg)', borderRadius: 'var(--r-sm)',
              padding: '10px 12px', border: '1px solid var(--divider)',
            }}>
              <code
                onClick={() => setShowToken(!showToken)}
                style={{
                  flex: 1, fontFamily: 'var(--font-mono)', fontSize: '0.82rem',
                  cursor: 'pointer', wordBreak: 'break-all',
                }}
              >
                {showToken ? config.api_token : maskedToken}
              </code>
              <CopyButton text={config.api_token} />
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-3)', marginTop: '4px' }}>
              Tap token to reveal. Only visible to admins.
            </div>
          </div>
        )}

        {!config.api_token && config.api_token_set && (
          <div style={{
            fontSize: '0.8rem', color: 'var(--text-3)', fontStyle: 'italic',
            padding: '8px 0',
          }}>
            API token is set but only visible to admin users.
          </div>
        )}

        <div style={{
          display: 'flex', gap: '12px', flexWrap: 'wrap',
          fontSize: '0.78rem', color: 'var(--text-3)',
        }}>
          <span>{config.tools_count} tools available</span>
          <span style={{ color: 'var(--divider)' }}>|</span>
          <span>{config.deployment === 'local' ? 'Local (SQLite)' : 'Docker (PostgreSQL)'}</span>
        </div>
      </div>

      {/* Claude Desktop Setup */}
      <div className="card">
        <div className="section-label">Claude Desktop</div>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-2)', marginBottom: '12px' }}>
          Add this to your Claude Desktop MCP config:
        </p>
        <CodeBlock copyText={claudeDesktopConfig}>
          {claudeDesktopConfig}
        </CodeBlock>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-3)', marginTop: '10px' }}>
          On macOS: <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
            ~/Library/Application Support/Claude/claude_desktop_config.json
          </code>
        </p>
      </div>

      {/* Claude Code Setup */}
      <div className="card">
        <div className="section-label">Claude Code</div>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-2)', marginBottom: '12px' }}>
          Add the MCP server from your terminal:
        </p>
        <CodeBlock copyText={`claude mcp add diligence --transport sse ${config.mcp_url}`}>
          {`claude mcp add diligence --transport sse ${config.mcp_url}`}
        </CodeBlock>
      </div>

      {/* What your agent can do */}
      <div className="card">
        <div className="section-label">What Your Agent Can Do</div>
        <div style={{ display: 'grid', gap: '8px' }}>
          {[
            ['Log workouts', 'Track any activity and earn points automatically'],
            ['Track food', 'Search 400K+ foods, log meals with full macros'],
            ['Manage meal plans', 'Create plans, track compliance, adjust portions'],
            ['Check progress', 'Daily points, weekly summary, program status'],
            ['Redeem rewards', 'Spend earned points on rewards you set up'],
          ].map(([title, desc]) => (
            <div key={title} style={{
              display: 'flex', gap: '10px', alignItems: 'flex-start',
              padding: '8px 0', borderBottom: '1px solid var(--divider)',
            }}>
              <span style={{ color: 'var(--green)', fontSize: '0.9rem', marginTop: '1px' }}>
                &#10003;
              </span>
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>{title}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-3)' }}>{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
