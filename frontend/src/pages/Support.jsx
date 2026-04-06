import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

export default function Support() {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [input, setInput] = useState('')
  const [confirmation, setConfirmation] = useState(null)
  const bottomRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => { loadThread() }, [])
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function loadThread() {
    try {
      const data = await api.getThread()
      setMessages(data.messages || [])
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  async function handleSend(e) {
    e.preventDefault()
    const body = input.trim()
    if (!body || sending) return

    setSending(true)
    setConfirmation(null)
    try {
      const result = await api.sendSupportMessage(body)
      setInput('')
      setConfirmation(result.message)
      await loadThread()
    } catch (err) {
      setConfirmation(err.message)
    }
    finally { setSending(false) }
  }

  function formatTime(iso) {
    const d = new Date(iso)
    const now = new Date()
    const diff = now - d
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
      + ' ' + d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
  }

  if (loading) return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-3)' }}>Loading...</div>

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100dvh - 64px)', maxWidth: '600px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{
        padding: '16px', borderBottom: '1px solid var(--divider)',
        display: 'flex', alignItems: 'center', gap: '12px',
      }}>
        <button onClick={() => navigate('/')} style={{
          background: 'transparent', color: 'var(--text-3)', padding: '4px 0', fontSize: '1.2rem',
        }}>←</button>
        <div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>
            Support
          </h1>
          <p style={{ color: 'var(--text-3)', fontSize: '0.75rem', margin: 0 }}>
            Ask a question — we'll get back to you
          </p>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflow: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--text-3)', fontSize: '0.85rem', marginTop: '2rem' }}>
            <div style={{ fontSize: '2rem', marginBottom: '8px' }}>💬</div>
            No messages yet. Ask anything about your workouts, program, or the app.
          </div>
        )}

        {messages.map(m => (
          <div key={m.id} style={{
            display: 'flex',
            justifyContent: m.sender === 'user' ? 'flex-end' : 'flex-start',
          }}>
            <div style={{
              maxWidth: '80%',
              padding: '10px 14px',
              borderRadius: m.sender === 'user'
                ? 'var(--r) var(--r) 4px var(--r)'
                : 'var(--r) var(--r) var(--r) 4px',
              background: m.sender === 'user' ? 'var(--orange)' : 'var(--card)',
              color: m.sender === 'user' ? '#fff' : 'var(--text)',
              boxShadow: 'var(--shadow-1)',
              fontSize: '0.88rem',
              lineHeight: 1.5,
            }}>
              <div>{m.body}</div>
              <div style={{
                fontSize: '0.68rem', marginTop: '4px',
                opacity: 0.7, textAlign: 'right',
              }}>
                {formatTime(m.created_at)}
                {m.sender === 'user' && m.read_at && ' ✓'}
              </div>
            </div>
          </div>
        ))}

        {confirmation && (
          <div style={{
            textAlign: 'center', fontSize: '0.8rem', color: 'var(--green-dark)',
            padding: '8px', background: 'var(--green-ghost)', borderRadius: 'var(--r-sm)',
          }}>
            {confirmation}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSend} style={{
        padding: '12px 16px', borderTop: '1px solid var(--divider)',
        display: 'flex', gap: '8px', background: 'var(--card)',
      }}>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Type your question..."
          maxLength={2000}
          style={{
            flex: 1, padding: '12px 14px', borderRadius: 'var(--r-full)',
            border: '1px solid var(--divider)', fontFamily: 'var(--font)',
            fontSize: '0.88rem', background: 'var(--bg)',
          }}
        />
        <button
          type="submit"
          disabled={!input.trim() || sending}
          style={{
            background: sending ? 'var(--text-3)' : 'var(--orange)',
            color: '#fff', borderRadius: 'var(--r-full)',
            width: '44px', height: '44px', padding: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1.1rem', boxShadow: 'var(--shadow-orange)',
            opacity: !input.trim() ? 0.5 : 1,
          }}
        >
          ↑
        </button>
      </form>
    </div>
  )
}
