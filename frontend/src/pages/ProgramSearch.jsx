import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

const DIFFICULTY_COLORS = {
  beginner: 'var(--green)',
  intermediate: 'var(--blue)',
  advanced: 'var(--purple)',
}

const CATEGORY_ICONS = {
  strength: '🏋️',
  cardio: '🏃',
  flexibility: '🧘',
  hybrid: '⚡',
}

const STATUS_LABELS = {
  pending: { label: 'Queued', color: 'var(--amber)' },
  crawling: { label: 'Fetching...', color: 'var(--blue)' },
  extracting: { label: 'Analyzing...', color: 'var(--purple)' },
  ready: { label: 'Ready', color: 'var(--green)' },
  failed: { label: 'Failed', color: 'var(--red)' },
}

export default function ProgramSearch() {
  const [query, setQuery] = useState('')
  const [catalog, setCatalog] = useState([])
  const [userPrograms, setUserPrograms] = useState([])
  const [loading, setLoading] = useState(true)
  const [researching, setResearching] = useState(false)
  const [message, setMessage] = useState(null)
  const navigate = useNavigate()

  useEffect(() => { loadData() }, [])

  async function loadData() {
    try {
      const [cat, progs] = await Promise.all([
        api.searchCatalog(''),
        api.listPrograms(),
      ])
      setCatalog(cat)
      setUserPrograms(progs)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  async function handleSearch(e) {
    e.preventDefault()
    if (!query.trim()) return
    try {
      const results = await api.searchCatalog(query)
      setCatalog(results)
    } catch (err) { console.error(err) }
  }

  async function handleResearch() {
    if (!query.trim()) return
    setResearching(true)
    setMessage(null)
    try {
      const result = await api.researchProgram(query)
      if (result.already_exists) {
        setMessage({ type: 'info', text: `"${result.name}" is already in the catalog.` })
      } else {
        setMessage({
          type: 'success',
          text: result.message || 'Program queued for research!',
        })
      }
      await loadData()
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    }
    finally { setResearching(false) }
  }

  async function handleAdopt(catalogId) {
    const today = new Date().toISOString().slice(0, 10)
    try {
      await api.adoptProgram(catalogId, today)
      setMessage({ type: 'success', text: 'Program started! Check your dashboard.' })
      await loadData()
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    }
  }

  // Check if user already has a catalog program active
  function isAdopted(catalogId) {
    return userPrograms.some(p => p.status === 'active' && p.catalog_id === catalogId)
  }

  if (loading) return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-3)' }}>Loading...</div>

  return (
    <div style={{ padding: '1rem', paddingBottom: '96px', maxWidth: '600px', margin: '0 auto' }}>
      {/* Header */}
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.6rem', fontWeight: 900, marginBottom: '0.5rem' }}>
        Programs
      </h1>
      <p style={{ color: 'var(--text-3)', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
        Find a program or tell us what you're doing — we'll set it up for you.
      </p>

      {/* Search / Research */}
      <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder='e.g. "StrongLifts 5x5" or "Couch to 5K"'
          style={{
            flex: 1, padding: '12px 16px', borderRadius: 'var(--r)', border: '1px solid var(--divider)',
            fontFamily: 'var(--font)', fontSize: '0.9rem', background: 'var(--card)',
          }}
        />
        <button type="submit" style={{
          background: 'var(--blue)', color: '#fff', padding: '12px 18px',
          boxShadow: 'var(--shadow-1)',
        }}>Search</button>
      </form>

      <button
        onClick={handleResearch}
        disabled={researching || !query.trim()}
        style={{
          width: '100%', background: researching ? 'var(--text-3)' : 'var(--orange)',
          color: '#fff', padding: '14px', marginBottom: '1rem',
          boxShadow: researching ? 'none' : 'var(--shadow-orange)',
          opacity: !query.trim() ? 0.5 : 1,
        }}
      >
        {researching ? 'Researching...' : `Research "${query || '...'}" for me`}
      </button>

      {/* Message */}
      {message && (
        <div style={{
          padding: '12px 16px', borderRadius: 'var(--r-sm)', marginBottom: '1rem',
          fontSize: '0.85rem', fontWeight: 600,
          background: message.type === 'error' ? 'var(--red-ghost)' : message.type === 'success' ? 'var(--green-ghost)' : 'var(--blue-ghost)',
          color: message.type === 'error' ? 'var(--red)' : message.type === 'success' ? 'var(--green-dark)' : 'var(--blue)',
        }}>
          {message.text}
        </div>
      )}

      {/* Active Programs */}
      {userPrograms.filter(p => p.status === 'active').length > 0 && (
        <>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 800, marginBottom: '0.75rem' }}>
            Your Active Programs
          </h2>
          {userPrograms.filter(p => p.status === 'active').map(p => (
            <div
              key={p.id}
              onClick={() => navigate(`/programs/${p.id}`)}
              style={{
                background: 'var(--card)', borderRadius: 'var(--r)', padding: '16px',
                marginBottom: '0.75rem', boxShadow: 'var(--shadow-1)', cursor: 'pointer',
                border: '2px solid var(--orange-glow)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong style={{ fontFamily: 'var(--font-display)', fontSize: '1rem' }}>{p.name}</strong>
                <span style={{ fontSize: '0.8rem', color: 'var(--orange)', fontWeight: 700 }}>
                  Day {p.current_day}/{p.total_days}
                </span>
              </div>
              <div style={{
                marginTop: '8px', height: '6px', borderRadius: '3px', background: 'var(--divider)',
              }}>
                <div style={{
                  height: '100%', borderRadius: '3px', background: 'var(--orange)',
                  width: `${Math.min(100, (p.current_day / p.total_days) * 100)}%`,
                  transition: 'width 0.3s ease',
                }} />
              </div>
            </div>
          ))}
        </>
      )}

      {/* Catalog */}
      <h2 style={{
        fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 800,
        marginTop: '1.5rem', marginBottom: '0.75rem',
      }}>
        Program Catalog
      </h2>

      {catalog.length === 0 && (
        <p style={{ color: 'var(--text-3)', fontSize: '0.85rem', textAlign: 'center', padding: '2rem 0' }}>
          No programs found. Try searching or researching a program above.
        </p>
      )}

      {catalog.map(p => {
        const status = STATUS_LABELS[p.crawl_status] || STATUS_LABELS.pending
        const adopted = isAdopted(p.id)
        return (
          <div key={p.id} style={{
            background: 'var(--card)', borderRadius: 'var(--r)', padding: '16px',
            marginBottom: '0.75rem', boxShadow: 'var(--shadow-1)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <strong style={{ fontFamily: 'var(--font-display)', fontSize: '1rem' }}>
                  {CATEGORY_ICONS[p.category] || '📋'} {p.name}
                </strong>
                {p.description && (
                  <p style={{ color: 'var(--text-2)', fontSize: '0.82rem', marginTop: '4px' }}>
                    {p.description}
                  </p>
                )}
              </div>
              <span style={{
                fontSize: '0.7rem', fontWeight: 700, padding: '3px 8px',
                borderRadius: 'var(--r-full)', color: '#fff', background: status.color,
                whiteSpace: 'nowrap',
              }}>
                {status.label}
              </span>
            </div>

            {/* Meta tags */}
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '10px' }}>
              {p.duration_weeks && (
                <span style={tagStyle}>{p.duration_weeks} weeks</span>
              )}
              {p.frequency_per_week && (
                <span style={tagStyle}>{p.frequency_per_week}x/week</span>
              )}
              {p.difficulty && (
                <span style={{
                  ...tagStyle,
                  color: DIFFICULTY_COLORS[p.difficulty] || 'var(--text-3)',
                  background: `${DIFFICULTY_COLORS[p.difficulty] || 'var(--text-3)'}11`,
                }}>
                  {p.difficulty}
                </span>
              )}
              {(p.equipment || []).slice(0, 3).map(eq => (
                <span key={eq} style={tagStyle}>{eq}</span>
              ))}
            </div>

            {/* Action button */}
            {p.crawl_status === 'ready' && !adopted && (
              <button
                onClick={() => handleAdopt(p.id)}
                style={{
                  marginTop: '12px', width: '100%', background: 'var(--green)', color: '#fff',
                  padding: '10px', fontSize: '0.85rem', boxShadow: 'var(--shadow-green)',
                }}
              >
                Start Program
              </button>
            )}
            {adopted && (
              <div style={{
                marginTop: '12px', textAlign: 'center', fontSize: '0.82rem',
                color: 'var(--green-dark)', fontWeight: 700,
              }}>
                ✓ Active
              </div>
            )}
            {p.crawl_status === 'ready' && (
              <button
                onClick={() => navigate(`/catalog/${p.id}`)}
                style={{
                  marginTop: adopted ? '4px' : '8px', width: '100%', background: 'transparent',
                  color: 'var(--blue)', padding: '8px', fontSize: '0.82rem',
                  border: '1px solid var(--divider)',
                }}
              >
                View Details
              </button>
            )}
          </div>
        )
      })}
    </div>
  )
}

const tagStyle = {
  fontSize: '0.72rem', fontWeight: 600, padding: '3px 10px',
  borderRadius: 'var(--r-full)', background: 'var(--divider)', color: 'var(--text-2)',
}
