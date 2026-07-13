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

const AI_PROVIDERS = [
  { name: 'OpenRouter', desc: '300+ models, one key. 26 free models.', url: 'https://openrouter.ai/keys', free: true },
  { name: 'Groq', desc: 'Ultra-fast Llama inference.', url: 'https://console.groq.com/keys', free: true },
  { name: 'Hugging Face', desc: 'Thousands of open-source models.', url: 'https://huggingface.co/settings/tokens', free: true },
  { name: 'Ollama', desc: 'Run LLMs locally. No key needed.', url: 'https://ollama.com/', free: true },
  { name: 'Google Gemini', desc: 'Gemini 2.0 Flash, 2.5 Pro.', url: 'https://aistudio.google.com/apikey', free: true },
  { name: 'OpenAI', desc: 'GPT-4o, GPT-4o-mini.', url: 'https://platform.openai.com/api-keys', free: false },
  { name: 'Anthropic Claude', desc: 'Claude Sonnet 4.6, Opus 4.8.', url: 'https://console.anthropic.com/', free: false },
  { name: 'Custom', desc: 'Any OpenAI-compatible endpoint.', url: '', free: false },
]

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

  const cursorConfig = JSON.stringify({
    "mcpServers": {
      "diligence": {
        "url": config.mcp_url,
        ...(config.api_token ? { "headers": { "Authorization": `Bearer ${config.api_token}` } } : {})
      }
    }
  }, null, 2)

  return (
    <div className="page">
      <a href="/settings/integrations" style={{
        fontSize: '0.82rem', color: 'var(--accent)', textDecoration: 'none',
        display: 'inline-block', marginBottom: '12px',
      }}>
        &larr; Back to Integrations
      </a>
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{
          fontFamily: 'var(--font-display)', fontWeight: 800,
          fontSize: '1.3rem', marginBottom: '4px',
        }}>
          Connect AI
        </h1>
        <p style={{ color: 'var(--text-3)', fontSize: '0.85rem' }}>
          Two ways to use AI with Diligence: the built-in chat, or an external agent.
        </p>
      </div>

      {/* === OPTION 1: Built-in AI Coach === */}
      <div className="card">
        <div className="section-label">Option 1 &mdash; Built-in AI Coach</div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-2)', marginBottom: '14px' }}>
          Get an API key from any provider below, paste it into{' '}
          <a href="/settings/integrations#ai-coaching" style={{ color: 'var(--accent)', fontWeight: 600 }}>
            Settings &rarr; Integrations
          </a>, then open the <strong>Coach</strong> tab. One key is all you need.
        </p>

        <div style={{ display: 'grid', gap: '8px' }}>
          {AI_PROVIDERS.map(p => (
            <div key={p.name} style={{
              display: 'flex', alignItems: 'center', gap: '10px',
              padding: '10px 0', borderBottom: '1px solid var(--divider)',
            }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.88rem' }}>{p.name}</span>
                  {p.free && (
                    <span style={{
                      fontSize: '0.6rem', padding: '1px 6px', borderRadius: 10,
                      background: 'var(--green-bg)', color: 'var(--green)',
                      fontWeight: 700, fontFamily: 'var(--font-mono)',
                    }}>FREE</span>
                  )}
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-3)' }}>{p.desc}</div>
              </div>
              {p.url && (
                <a href={p.url} target="_blank" rel="noopener noreferrer"
                  className="btn-outline btn-sm"
                  style={{ fontSize: '0.72rem', textDecoration: 'none', whiteSpace: 'nowrap' }}>
                  Get key &rarr;
                </a>
              )}
            </div>
          ))}
        </div>

        <p style={{ fontSize: '0.75rem', color: 'var(--text-3)', marginTop: '14px' }}>
          After getting a key: <strong>Settings &rarr; Integrations &rarr; AI Coaching</strong> &rarr; paste your key &rarr; open the <strong>Coach</strong> tab.
        </p>
      </div>

      {/* === OPTION 2: External AI Agents (MCP) === */}
      <div className="card">
        <div className="section-label">Option 2 &mdash; External AI Agent (MCP)</div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-2)', marginBottom: '14px' }}>
          Connect an MCP-compatible AI tool to control Diligence from outside the app.
          The agent can log workouts, track food, check progress, and manage rewards.
        </p>

        {/* Connection Details */}
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
      </div>

      {/* Claude Desktop */}
      <div className="card">
        <div className="section-label">Claude Desktop</div>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-2)', marginBottom: '12px' }}>
          Add this to your Claude Desktop MCP config:
        </p>
        <CodeBlock copyText={claudeDesktopConfig}>
          {claudeDesktopConfig}
        </CodeBlock>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-3)', marginTop: '10px' }}>
          macOS: <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
            ~/Library/Application Support/Claude/claude_desktop_config.json
          </code><br />
          Windows: <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
            %APPDATA%\Claude\claude_desktop_config.json
          </code>
        </p>
      </div>

      {/* Claude Code */}
      <div className="card">
        <div className="section-label">Claude Code (CLI)</div>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-2)', marginBottom: '12px' }}>
          Add the MCP server from your terminal:
        </p>
        <CodeBlock copyText={`claude mcp add diligence --transport sse ${config.mcp_url}`}>
          {`claude mcp add diligence --transport sse ${config.mcp_url}`}
        </CodeBlock>
      </div>

      {/* Cursor */}
      <div className="card">
        <div className="section-label">Cursor</div>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-2)', marginBottom: '12px' }}>
          Add to <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>.cursor/mcp.json</code> in your project:
        </p>
        <CodeBlock copyText={cursorConfig}>
          {cursorConfig}
        </CodeBlock>
      </div>

      {/* Windsurf / Other */}
      <div className="card">
        <div className="section-label">Windsurf / Other MCP Tools</div>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-2)', marginBottom: '12px' }}>
          Any MCP-compatible tool can connect using the endpoint and token above.
          Use the same JSON format as Cursor &mdash; add a server named "diligence"
          pointing to the MCP endpoint URL.
        </p>
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
        <div style={{ fontSize: '0.72rem', color: 'var(--text-3)', marginTop: '12px' }}>
          {config.tools_count} tools available &middot; {config.deployment === 'local' ? 'Local (SQLite)' : 'Docker (PostgreSQL)'}
        </div>
      </div>
    </div>
  )
}
