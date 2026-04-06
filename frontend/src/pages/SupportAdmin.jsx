import { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'

export default function SupportAdmin() {
  const { threadId } = useParams()

  // If threadId is present, show the thread detail; otherwise show thread list
  if (threadId) return <AdminThread threadId={threadId} />
  return <AdminThreadList />
}


function AdminThreadList() {
  const [threads, setThreads] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => { loadThreads() }, [])

  async function loadThreads() {
    try {
      const data = await api.listSupportThreads()
      setThreads(data)
    } catch (err) {
      setError(err.message)
    }
    finally { setLoading(false) }
  }

  if (loading) return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-3)' }}>Loading...</div>
  if (error) return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--red)' }}>{error}</div>

  return (
    <div style={{ padding: '1rem', maxWidth: '600px', margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '1.5rem' }}>
        <button onClick={() => navigate('/')} style={{
          background: 'transparent', color: 'var(--text-3)', padding: '4px 0', fontSize: '1.2rem',
        }}>←</button>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.4rem', fontWeight: 900, margin: 0 }}>
          Support Inbox
        </h1>
      </div>

      {threads.length === 0 && (
        <p style={{ textAlign: 'center', color: 'var(--text-3)', fontSize: '0.85rem', marginTop: '3rem' }}>
          No support conversations yet.
        </p>
      )}

      {threads.map(t => (
        <div
          key={t.id}
          onClick={() => navigate(`/support/admin/${t.id}`)}
          style={{
            background: 'var(--card)', borderRadius: 'var(--r)', padding: '14px 16px',
            marginBottom: '0.6rem', boxShadow: 'var(--shadow-1)', cursor: 'pointer',
            border: t.unread_admin > 0 ? '2px solid var(--orange-glow)' : '1px solid var(--card-border)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong style={{ fontFamily: 'var(--font-display)', fontSize: '0.95rem' }}>
              {t.user_name}
            </strong>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {t.unread_admin > 0 && (
                <span style={{
                  background: 'var(--orange)', color: '#fff', fontSize: '0.65rem', fontWeight: 800,
                  width: '20px', height: '20px', borderRadius: '50%',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>{t.unread_admin}</span>
              )}
              <span style={{ fontSize: '0.72rem', color: 'var(--text-3)' }}>
                {t.message_count} msgs
              </span>
            </div>
          </div>
          {t.last_message && (
            <p style={{
              color: 'var(--text-2)', fontSize: '0.82rem', marginTop: '4px',
              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            }}>
              <span style={{ color: 'var(--text-3)', fontWeight: 600 }}>
                {t.last_message.sender === 'admin' ? 'You: ' : ''}
              </span>
              {t.last_message.body}
            </p>
          )}
        </div>
      ))}
    </div>
  )
}


function AdminThread({ threadId }) {
  const [thread, setThread] = useState(null)
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => { loadThread() }, [threadId])
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [thread])

  async function loadThread() {
    try {
      const data = await api.getAdminThread(threadId)
      setThread(data)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  async function handleReply(e) {
    e.preventDefault()
    const body = input.trim()
    if (!body || sending) return
    setSending(true)
    try {
      await api.replySupportThread(threadId, body)
      setInput('')
      await loadThread()
    } catch (err) { alert(err.message) }
    finally { setSending(false) }
  }

  function formatTime(iso) {
    const d = new Date(iso)
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
      + ' ' + d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
  }

  if (loading) return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-3)' }}>Loading...</div>
  if (!thread) return <div style={{ padding: '2rem', textAlign: 'center' }}>Thread not found</div>

  const ctx = thread.latest_context || {}

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100dvh - 64px)', maxWidth: '600px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{
        padding: '14px 16px', borderBottom: '1px solid var(--divider)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button onClick={() => navigate('/support/admin')} style={{
            background: 'transparent', color: 'var(--text-3)', padding: '4px 0', fontSize: '1.2rem',
          }}>←</button>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 800, margin: 0 }}>
            {thread.user_name}
          </h2>
        </div>

        {/* Context bar */}
        {ctx.program_name && (
          <div style={{
            display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '8px', marginLeft: '36px',
          }}>
            <span style={ctxTag}>{ctx.program_name}</span>
            {ctx.program_day && (
              <span style={ctxTag}>Day {ctx.program_day}/{ctx.program_total_days}</span>
            )}
            {ctx.program_completion_pct !== undefined && (
              <span style={ctxTag}>{ctx.program_completion_pct}%</span>
            )}
            <span style={{
              ...ctxTag,
              background: ctx.gate_passed ? 'var(--green-ghost)' : 'var(--red-ghost)',
              color: ctx.gate_passed ? 'var(--green-dark)' : 'var(--red)',
            }}>
              {ctx.points_today}/{ctx.daily_target} pts {ctx.gate_passed ? '✓' : '✗'}
            </span>
            {ctx.last_workout && (
              <span style={ctxTag}>Last: {ctx.last_workout}</span>
            )}
          </div>
        )}
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflow: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {(thread.messages || []).map(m => (
          <div key={m.id} style={{
            display: 'flex',
            justifyContent: m.sender === 'admin' ? 'flex-end' : 'flex-start',
          }}>
            <div style={{
              maxWidth: '80%',
              padding: '10px 14px',
              borderRadius: m.sender === 'admin'
                ? 'var(--r) var(--r) 4px var(--r)'
                : 'var(--r) var(--r) var(--r) 4px',
              background: m.sender === 'admin' ? 'var(--blue)' : 'var(--card)',
              color: m.sender === 'admin' ? '#fff' : 'var(--text)',
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
                {m.read_at && ' ✓'}
              </div>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Reply input */}
      <form onSubmit={handleReply} style={{
        padding: '12px 16px', borderTop: '1px solid var(--divider)',
        display: 'flex', gap: '8px', background: 'var(--card)',
      }}>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Reply..."
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
            background: sending ? 'var(--text-3)' : 'var(--blue)',
            color: '#fff', borderRadius: 'var(--r-full)',
            width: '44px', height: '44px', padding: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1.1rem',
            opacity: !input.trim() ? 0.5 : 1,
          }}
        >
          ↑
        </button>
      </form>
    </div>
  )
}


const ctxTag = {
  fontSize: '0.68rem', fontWeight: 600, padding: '2px 8px',
  borderRadius: 'var(--r-full)', background: 'var(--divider)', color: 'var(--text-2)',
}
