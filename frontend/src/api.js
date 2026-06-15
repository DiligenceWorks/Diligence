const API_BASE = '/api';

function getToken() {
  return localStorage.getItem('fitness_token');
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const resp = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (resp.status === 401) {
    localStorage.removeItem('fitness_token');
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }

  return resp.json();
}

export const api = {
  // Auth
  login: (username, password) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
  register: (username, password, display_name) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify({ username, password, display_name }) }),
  me: () => request('/auth/me'),

  // Onboarding
  onboardingStatus: () => request('/onboarding/status'),
  savePhase1: (data) => request('/onboarding/phase1', { method: 'POST', body: JSON.stringify(data) }),
  savePhase2: (data) => request('/onboarding/phase2', { method: 'POST', body: JSON.stringify(data) }),
  getRecommendations: () => request('/onboarding/recommendations'),

  // Points
  today: () => request('/points/today'),
  week: (start) => request(`/points/week${start ? `?start=${start}` : ''}`),
  getRules: () => request('/points/rules'),
  updateRule: (id, data) => request(`/points/rules/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  getTargets: () => request('/points/targets'),
  updateTargets: (data) => request('/points/targets', { method: 'PATCH', body: JSON.stringify(data) }),

  // Activities
  listActivities: (date) => request(`/activities${date ? `?date=${date}` : ''}`),
  logActivity: (data) => request('/activities', { method: 'POST', body: JSON.stringify(data) }),
  deleteActivity: (id) => request(`/activities/${id}`, { method: 'DELETE' }),

  // Food
  listFood: (date) => request(`/food${date ? `?date=${date}` : ''}`),
  logFood: (data) => request('/food', { method: 'POST', body: JSON.stringify(data) }),
  deleteFood: (id) => request(`/food/${id}`, { method: 'DELETE' }),
  scanBarcode: (barcode) => request(`/food/scan/${barcode}`),
  searchFood: (q) => request(`/food/search?q=${encodeURIComponent(q)}`),

  // Nutrition (v3: keto + fasting)
  nutritionToday: () => request('/nutrition/today'),
  getNutritionGoals: () => request('/nutrition/goals'),
  updateNutritionGoals: (data) => request('/nutrition/goals', { method: 'PATCH', body: JSON.stringify(data) }),
  startFast: (data) => request('/nutrition/fasts', { method: 'POST', body: JSON.stringify(data) }),
  endFast: (id, data) => request(`/nutrition/fasts/${id}`, { method: 'PATCH', body: JSON.stringify(data || {}) }),
  listFasts: (limit) => request(`/nutrition/fasts${limit ? `?limit=${limit}` : ''}`),
  getActiveFast: () => request('/nutrition/fasts/active'),
  deleteFast: (id) => request(`/nutrition/fasts/${id}`, { method: 'DELETE' }),
  logElectrolytes: (data) => request('/nutrition/electrolytes', { method: 'POST', body: JSON.stringify(data) }),
  getElectrolytesToday: () => request('/nutrition/electrolytes/today'),

  // Rewards
  listRewards: () => request('/rewards'),
  createReward: (data) => request('/rewards', { method: 'POST', body: JSON.stringify(data) }),
  redeemReward: (id, date) => request(`/rewards/${id}/redeem`, { method: 'POST', body: JSON.stringify({ date }) }),

  // Programs (v1)
  listPrograms: () => request('/programs'),
  createProgram: (data) => request('/programs', { method: 'POST', body: JSON.stringify(data) }),
  getProgram: (id) => request(`/programs/${id}`),

  // Program Catalog (v2)
  searchCatalog: (q) => request(`/programs/catalog${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  getCatalogProgram: (id) => request(`/programs/catalog/${id}`),
  researchProgram: (name) =>
    request('/programs/research', { method: 'POST', body: JSON.stringify({ name }) }),
  adoptProgram: (catalogId, startDate) =>
    request(`/programs/catalog/${catalogId}/adopt`, {
      method: 'POST', body: JSON.stringify({ start_date: startDate }),
    }),

  // Program Tracking (v2)
  getProgramSchedule: (id) => request(`/programs/${id}/schedule`),
  getWorkoutDetail: (progId, workoutId) => request(`/programs/${progId}/workout/${workoutId}`),
  completeWorkout: (progId, workoutId, data) =>
    request(`/programs/${progId}/workout/${workoutId}/complete`, {
      method: 'POST', body: JSON.stringify(data),
    }),
  getProgramProgress: (id) => request(`/programs/${id}/progress`),

  // Support (user)
  getThread: () => request('/support/thread'),
  sendSupportMessage: (body) =>
    request('/support/messages', { method: 'POST', body: JSON.stringify({ body }) }),
  getUnreadCount: () => request('/support/unread'),

  // Support (admin)
  listSupportThreads: () => request('/support/admin/threads'),
  getAdminThread: (threadId) => request(`/support/admin/threads/${threadId}`),
  replySupportThread: (threadId, body) =>
    request(`/support/admin/threads/${threadId}/reply`, {
      method: 'POST', body: JSON.stringify({ body }),
    }),

  // Integrations
  integrationStatus: () => request('/integrations'),
  stravaAuth: () => request('/integrations/strava/auth'),
  stravaSync: () => request('/integrations/strava/sync', { method: 'POST' }),
  polarAuth: () => request('/integrations/polar/auth'),
  polarSync: () => request('/integrations/polar/sync', { method: 'POST' }),
  disconnect: (provider) => request(`/integrations/${provider}`, { method: 'DELETE' }),


  // Meal Plans (v3)
  listMealPlans: () => request('/meal-plans'),
  createMealPlan: (data) => request('/meal-plans', { method: 'POST', body: JSON.stringify(data) }),
  getMealPlanToday: () => request('/meal-plans/today'),
  getMealPlan: (id) => request('/meal-plans/' + id),
  updateMealPlanStatus: (id, status) =>
    request('/meal-plans/' + id, { method: 'PATCH', body: JSON.stringify({ status }) }),
  logMealCompliance: (data) =>
    request('/meal-plans/compliance', { method: 'POST', body: JSON.stringify(data) }),
  getMealPlanProgress: (id) => request('/meal-plans/' + id + '/progress'),

  // Dynamic Integrations (v3)
  fullIntegrationStatus: () => request('/integrations/status'),
  listProviders: () => request('/integrations/providers'),
  configureIntegration: (provider, credentials) =>
    request('/integrations/configure', { method: 'POST', body: JSON.stringify({ provider, credentials }) }),
  // Resources
  getResourceRecommendations: () => request('/onboarding/recommendations'),
};

export function setToken(token) {
  localStorage.setItem('fitness_token', token);
}

export function clearToken() {
  localStorage.removeItem('fitness_token');
}

export function hasToken() {
  return !!localStorage.getItem('fitness_token');
}
