import { useState, useEffect, useRef } from 'react'
import { api } from '../api'

export default function ChatCoach() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [aiStatus, setAiStatus] = useState(null)
  const scrollRef = useRef(null)

  useEffect(() => {
    api.getAIStatus().then(setAiStatus).catch(() => setAiStatus({ configured: false }))
  }, [])

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || streaming) return

    const userMsg = { role: 'user', content: text }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setStreaming(true)

    // Add placeholder for assistant
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }))
      const token = localStorage.getItem('fitness_token')
      const resp = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: text, history }),
      })

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ') && line.trim() !== 'data: [DONE]') {
            try {
              const { text: chunk } = JSON.parse(line.slice(6))
              if (chunk) {
                setMessages(prev => {
                  const updated = [...prev]
                  const last = updated[updated.length - 1]
                  updated[updated.length - 1] = { ...last, content: last.content + chunk }
                  return updated
                })
              }
            } catch {}
          }
        }
      }
    } catch (err) {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          role: 'assistant',
          content: 'Connection error. Check that the backend is running and an AI provider is configured in Settings → Integrations.',
        }
        return updated
      })
    }
    setStreaming(false)
  }

  const suggestions = [
    'What should I eat today?',
    'Log my 30-minute run',
    'How am I doing this week?',
    'Create a meal plan for me',
  ]

  if (aiStatus && !aiStatus.configured) {
    return (
      <div className="page">
        <h1 className="page-title">AI Coach</h1>
        <div className="card" style={{ textAlign: 'center', padding: '32px 20px' }}>
          <div style={{ fontSize: '2rem', marginBottom: '12px' }}>🤖</div>
          <h3 style={{ marginBottom: '8px' }}>No AI provider connected</h3>
          <p style={{ color: 'var(--text-2)', fontSize: '0.9rem', marginBottom: '16px' }}>
            Connect OpenAI, OpenRouter, Claude, Ollama, or any other provider to start chatting with your AI fitness coach.
          </p>
          <a href="/settings/integrations" className="btn-primary" style={{
            display: 'inline-block', padding: '12px 24px', borderRadius: 'var(--r)',
            background: 'var(--accent)', color: 'var(--text-inv)', textDecoration: 'none',
            fontWeight: 600, fontSize: '0.88rem',
          }}>
            Configure AI Provider
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="page" style={{ display: 'flex', flexDirection: 'column', paddingBottom: '96px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>AI Coach</h1>
        {aiStatus?.provider && (
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-3)',
            background: 'var(--accent-bg)', padding: '4px 10px', borderRadius: 'var(--r-full)',
          }}>
            {aiStatus.provider} · {aiStatus.model}
          </span>
        )}
      </div>

      <div style={{ flex: 1, overflowY: 'auto', marginBottom: '12px' }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', padding: '24px 0' }}>
            <p style={{ color: 'var(--text-3)', fontSize: '0.9rem', marginBottom: '16px' }}>
              Ask me anything about your fitness, nutrition, or program.
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center' }}>
              {suggestions.map(s => (
                <button key={s} className="btn-outline btn-sm" onClick={() => { setInput(s); }}
                  style={{ fontSize: '0.8rem' }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} style={{
            display: 'flex',
            justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            marginBottom: '10px',
          }}>
            <div style={{
              maxWidth: '85%',
              padding: '10px 14px',
              borderRadius: msg.role === 'user'
                ? 'var(--r-lg) var(--r-lg) var(--r-sm) var(--r-lg)'
                : 'var(--r-lg) var(--r-lg) var(--r-lg) var(--r-sm)',
              background: msg.role === 'user' ? 'var(--accent)' : 'var(--card)',
              color: msg.role === 'user' ? 'var(--text-inv)' : 'var(--text)',
              border: msg.role === 'user' ? 'none' : '1px solid var(--card-border)',
              fontSize: '0.9rem',
              lineHeight: '1.5',
              whiteSpace: 'pre-wrap',
            }}>
              {msg.content || (streaming && i === messages.length - 1 ? '...' : '')}
            </div>
          </div>
        ))}
        <div ref={scrollRef} />
      </div>

      <div style={{
        display: 'flex', gap: '8px',
        position: 'sticky', bottom: '72px',
        background: 'var(--bg)', padding: '8px 0',
      }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
          placeholder={streaming ? 'Thinking...' : 'Ask your AI coach...'}
          disabled={streaming}
          style={{ flex: 1 }}
        />
        <button
          onClick={sendMessage}
          disabled={streaming || !input.trim()}
          className="btn-primary"
          style={{ padding: '12px 18px', minWidth: 'auto' }}
        >
          {streaming ? '···' : '→'}
        </button>
      </div>
    </div>
  )
}
