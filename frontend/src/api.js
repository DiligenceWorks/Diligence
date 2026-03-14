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

  // Rewards
  listRewards: () => request('/rewards'),
  createReward: (data) => request('/rewards', { method: 'POST', body: JSON.stringify(data) }),
  redeemReward: (id, date) => request(`/rewards/${id}/redeem`, { method: 'POST', body: JSON.stringify({ date }) }),

  // Programs
  listPrograms: () => request('/programs'),
  createProgram: (data) => request('/programs', { method: 'POST', body: JSON.stringify(data) }),
  getProgram: (id) => request(`/programs/${id}`),

  // Integrations
  integrationStatus: () => request('/integrations'),
  stravaAuth: () => request('/integrations/strava/auth'),
  stravaSync: () => request('/integrations/strava/sync', { method: 'POST' }),
  polarAuth: () => request('/integrations/polar/auth'),
  polarSync: () => request('/integrations/polar/sync', { method: 'POST' }),
  disconnect: (provider) => request(`/integrations/${provider}`, { method: 'DELETE' }),

  // Resources
  getRecommendations: () => request('/onboarding/recommendations'),
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
