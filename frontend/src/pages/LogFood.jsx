import { useState, useEffect, useRef } from 'react'
import { api } from '../api'

const MEALS = ['breakfast', 'lunch', 'dinner', 'snack']

export default function LogFood() {
  const [tab, setTab] = useState('log')  // log, scan, search
  const [mealType, setMealType] = useState('lunch')
  const [foodName, setFoodName] = useState('')
  const [brand, setBrand] = useState('')
  const [calories, setCalories] = useState('')
  const [protein, setProtein] = useState('')
  const [carbs, setCarbs] = useState('')
  const [fat, setFat] = useState('')
  const [servings, setServings] = useState('1')
  const [barcode, setBarcode] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [todayFood, setTodayFood] = useState(null)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState('')

  useEffect(() => { loadToday() }, [])

  async function loadToday() {
    try {
      const today = new Date().toISOString().split('T')[0]
      const data = await api.listFood(today)
      setTodayFood(data)
    } catch (err) { console.error(err) }
  }

  function fillFromProduct(product) {
    setFoodName(product.product_name || '')
    setBrand(product.brand || '')
    setCalories(product.calories_100g ? String(Math.round(product.calories_100g)) : '')
    setProtein(product.protein_100g ? String(Math.round(product.protein_100g)) : '')
    setCarbs(product.carbs_100g ? String(Math.round(product.carbs_100g)) : '')
    setFat(product.fat_100g ? String(Math.round(product.fat_100g)) : '')
    setTab('log')
  }

  async function handleScan() {
    if (!barcode.trim()) return
    setLoading(true)
    try {
      const product = await api.scanBarcode(barcode.trim())
      fillFromProduct(product)
    } catch (err) { alert('Product not found. Try manual entry.') }
    finally { setLoading(false) }
  }

  async function handleSearch() {
    if (!searchQuery.trim()) return
    setLoading(true)
    try {
      const data = await api.searchFood(searchQuery)
      setSearchResults(data.results || [])
    } catch (err) { alert(err.message) }
    finally { setLoading(false) }
  }

  async function handleLog(e) {
    e.preventDefault()
    if (!foodName.trim()) return
    setLoading(true)
    try {
      const today = new Date().toISOString().split('T')[0]
      await api.logFood({
        meal_type: mealType,
        food_name: foodName,
        brand: brand || null,
        calories: calories ? parseFloat(calories) * parseFloat(servings || 1) : null,
        protein_g: protein ? parseFloat(protein) * parseFloat(servings || 1) : null,
        carbs_g: carbs ? parseFloat(carbs) * parseFloat(servings || 1) : null,
        fat_g: fat ? parseFloat(fat) * parseFloat(servings || 1) : null,
        servings: parseFloat(servings || 1),
        food_date: today,
      })
      setSuccess('Food logged!')
      setFoodName(''); setBrand(''); setCalories(''); setProtein(''); setCarbs(''); setFat(''); setServings('1')
      await loadToday()
      setTimeout(() => setSuccess(''), 2000)
    } catch (err) { alert(err.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="page">
      <h1 className="page-title">Food Log</h1>

      {success && <div style={{ padding: '10px', background: 'rgba(74,222,128,0.1)', borderRadius: 'var(--radius-sm)', color: 'var(--success)', textAlign: 'center', marginBottom: '12px', fontWeight: 600 }}>{success}</div>}

      {/* Tab bar */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <button className={tab === 'log' ? 'btn-primary btn-sm' : 'btn-outline btn-sm'} onClick={() => setTab('log')}>Manual</button>
        <button className={tab === 'scan' ? 'btn-primary btn-sm' : 'btn-outline btn-sm'} onClick={() => setTab('scan')}>📷 Scan</button>
        <button className={tab === 'search' ? 'btn-primary btn-sm' : 'btn-outline btn-sm'} onClick={() => setTab('search')}>🔍 Search</button>
      </div>

      {/* Barcode scan */}
      {tab === 'scan' && (
        <div className="card">
          <div className="form-group">
            <label className="form-label">Barcode number</label>
            <input value={barcode} onChange={e => setBarcode(e.target.value)} placeholder="Enter or scan barcode" inputMode="numeric" />
          </div>
          <button className="btn-primary btn-full" onClick={handleScan} disabled={loading}>
            {loading ? 'Looking up...' : 'Lookup'}
          </button>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '8px', textAlign: 'center' }}>
            Powered by Open Food Facts (4M+ products)
          </p>
        </div>
      )}

      {/* Food search */}
      {tab === 'search' && (
        <div className="card">
          <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
            <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Search foods..." onKeyDown={e => e.key === 'Enter' && handleSearch()} />
            <button className="btn-primary btn-sm" onClick={handleSearch} disabled={loading}>Go</button>
          </div>
          {searchResults.map((r, i) => (
            <div key={i} style={{ padding: '10px 0', borderBottom: '1px solid var(--border)', cursor: 'pointer' }} onClick={() => fillFromProduct(r)}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{r.product_name || 'Unknown'}</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {r.brand && `${r.brand} · `}{r.calories_100g ? `${Math.round(r.calories_100g)} cal/100g` : ''}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Manual log form */}
      {tab === 'log' && (
        <form onSubmit={handleLog}>
          <div className="card">
            <div className="form-group">
              <label className="form-label">Meal</label>
              <div style={{ display: 'flex', gap: '6px' }}>
                {MEALS.map(m => (
                  <button key={m} type="button" className={mealType === m ? 'btn-primary btn-sm' : 'btn-outline btn-sm'} onClick={() => setMealType(m)}>
                    {m.charAt(0).toUpperCase() + m.slice(1)}
                  </button>
                ))}
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Food name</label>
              <input value={foodName} onChange={e => setFoodName(e.target.value)} placeholder="e.g. Grilled chicken breast" required />
            </div>
            <div className="form-group">
              <label className="form-label">Brand (optional)</label>
              <input value={brand} onChange={e => setBrand(e.target.value)} placeholder="" />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div className="form-group">
                <label className="form-label">Calories</label>
                <input type="number" value={calories} onChange={e => setCalories(e.target.value)} placeholder="per serving" />
              </div>
              <div className="form-group">
                <label className="form-label">Servings</label>
                <input type="number" step="0.5" value={servings} onChange={e => setServings(e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">Protein (g)</label>
                <input type="number" value={protein} onChange={e => setProtein(e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">Carbs (g)</label>
                <input type="number" value={carbs} onChange={e => setCarbs(e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">Fat (g)</label>
                <input type="number" value={fat} onChange={e => setFat(e.target.value)} />
              </div>
            </div>
            <button type="submit" className="btn-primary btn-full" disabled={loading}>
              {loading ? 'Saving...' : 'Log Food'}
            </button>
          </div>
        </form>
      )}

      {/* Today's summary */}
      {todayFood && (
        <div className="card" style={{ marginTop: '8px' }}>
          <div style={{ fontWeight: 700, marginBottom: '10px' }}>
            Today: {Math.round(todayFood.total_calories)} cal
          </div>
          {MEALS.map(m => {
            const items = todayFood.meals[m] || []
            if (items.length === 0) return null
            return (
              <div className="meal-section" key={m}>
                <div className="meal-title">{m}</div>
                {items.map(item => (
                  <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: '0.9rem' }}>
                    <span>{item.food_name}</span>
                    <span style={{ color: 'var(--text-muted)' }}>{item.calories ? `${Math.round(item.calories)} cal` : ''}</span>
                  </div>
                ))}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
