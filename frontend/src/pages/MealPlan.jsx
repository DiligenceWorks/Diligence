import { useState, useEffect } from 'react'
import { api } from '../api'

const MEAL_ICONS = { breakfast: '🌅', lunch: '🌞', dinner: '🌙', snack: '🍎' }

export default function MealPlan() {
  const [plan, setPlan] = useState(null)
  const [plans, setPlans] = useState([])
  const [loading, setLoading] = useState(true)
  const [compliance, setCompliance] = useState({})  // plan_item_id → status

  useEffect(() => { loadAll() }, [])

  async function loadAll() {
    try {
      const [today, all] = await Promise.all([api.getMealPlanToday(), api.listMealPlans()])
      setPlan(today)
      setPlans(all)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  async function markCompliance(itemId, status) {
    try {
      await api.logMealCompliance({ plan_item_id: itemId, status })
      setCompliance(prev => ({ ...prev, [itemId]: status }))
    } catch (err) { alert(`Failed: ${err.message}`) }
  }

  if (loading) return <div className="page"><div className="loading">Loading...</div></div>

  return (
    <div className="page" style={{ maxWidth: 600, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 8 }}>Meal Plan</h1>

      {!plan?.active_plan ? (
        <div style={{
          background: 'var(--surface-2)', borderRadius: 'var(--r-md)', padding: 32,
          textAlign: 'center', color: 'var(--text-2)',
        }}>
          <div style={{ fontSize: '2rem', marginBottom: 12 }}>🍽️</div>
          <p style={{ marginBottom: 8 }}>No active meal plan.</p>
          <p style={{ fontSize: '0.85rem' }}>
            Ask your AI agent to create one: "Generate a 7-day keto meal plan for me"
          </p>
        </div>
      ) : (
        <>
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            marginBottom: 20, color: 'var(--text-2)', fontSize: '0.9rem',
          }}>
            <span>{plan.active_plan}</span>
            <span style={{
              background: 'var(--accent)', color: '#fff', padding: '3px 10px',
              borderRadius: 20, fontSize: '0.75rem', fontWeight: 600,
            }}>
              Day {plan.day} / {plan.duration_days}
            </span>
          </div>

          {plan.daily_calories && (
            <div style={{
              background: 'var(--surface-2)', borderRadius: 'var(--r-sm)', padding: 12,
              marginBottom: 16, textAlign: 'center', fontSize: '0.85rem', color: 'var(--text-2)',
            }}>
              Target: {plan.daily_calories} cal · {plan.diet_type || 'balanced'}
            </div>
          )}

          {plan.meals?.length > 0 ? (
            plan.meals.map(meal => {
              const itemStatus = compliance[meal.id]
              return (
                <div key={meal.id} style={{
                  background: 'var(--surface-2)', borderRadius: 'var(--r-md)', padding: 16,
                  marginBottom: 10,
                  borderLeft: itemStatus === 'followed' ? '4px solid #4CAF50' :
                    itemStatus === 'skipped' ? '4px solid #F44336' :
                    itemStatus === 'substituted' ? '4px solid #FF9800' : '4px solid transparent',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-3)', textTransform: 'uppercase', marginBottom: 4 }}>
                        {MEAL_ICONS[meal.meal_type] || '🍽️'} {meal.meal_type}
                      </div>
                      <div style={{ fontWeight: 600, marginBottom: 4 }}>{meal.food_name}</div>
                      {meal.description && (
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-2)' }}>{meal.description}</div>
                      )}
                    </div>
                    {meal.calories && (
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-2)', flexShrink: 0, marginLeft: 12 }}>
                        {meal.calories} cal
                      </div>
                    )}
                  </div>

                  {meal.protein_g && (
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-3)', marginTop: 6 }}>
                      P: {meal.protein_g}g · C: {meal.carbs_g}g · F: {meal.fat_g}g
                    </div>
                  )}

                  {!itemStatus && (
                    <div style={{ display: 'flex', gap: 6, marginTop: 10 }}>
                      {['followed', 'substituted', 'skipped'].map(s => (
                        <button key={s} onClick={() => markCompliance(meal.id, s)}
                          style={{
                            background: 'transparent', border: '1px solid var(--border)',
                            padding: '4px 12px', borderRadius: 'var(--r-sm)', fontSize: '0.75rem',
                            cursor: 'pointer', color: 'var(--text-2)', textTransform: 'capitalize',
                          }}>
                          {s === 'followed' ? '✅' : s === 'skipped' ? '⏭️' : '🔄'} {s}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )
            })
          ) : (
            <p style={{ color: 'var(--text-2)', textAlign: 'center' }}>{plan.message || 'No meals for today.'}</p>
          )}
        </>
      )}

      {plans.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 12 }}>All Plans</h2>
          {plans.map(p => (
            <div key={p.id} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '10px 0', borderBottom: '1px solid var(--border)',
            }}>
              <div>
                <div style={{ fontWeight: 500 }}>{p.name}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-3)' }}>
                  {p.diet_type} · {p.duration_days} days · started {p.start_date}
                </div>
              </div>
              <span style={{
                fontSize: '0.75rem', padding: '2px 8px', borderRadius: 12,
                background: p.status === 'active' ? '#4CAF5022' : '#9E9E9E22',
                color: p.status === 'active' ? '#4CAF50' : '#9E9E9E',
                fontWeight: 600,
              }}>
                {p.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
