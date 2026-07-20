const DEFAULT_API_BASE_URL = import.meta.env.PROD ? '/api/v1' : 'http://localhost:5000/api/v1';
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/$/, '');
const TOKEN_KEY = 'resq-command-token';

let accessToken = localStorage.getItem(TOKEN_KEY) || '';

function rememberSession(body) {
  accessToken = body.token;
  localStorage.setItem(TOKEN_KEY, accessToken);
  return body;
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...options.headers,
    },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.error || `Request failed with status ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return body;
}

export async function openDemoSession(role) {
  const body = await request('/auth/demo-session', { method: 'POST', body: JSON.stringify({ role }) });
  return rememberSession(body);
}

export async function login(payload) {
  return rememberSession(await request('/auth/login', { method: 'POST', body: JSON.stringify(payload) }));
}

export async function register(payload) {
  return rememberSession(await request('/auth/register', { method: 'POST', body: JSON.stringify(payload) }));
}

export const api = {
  bootstrap: () => request('/operations/bootstrap'),
  createDisaster: (payload) => request('/disasters', { method: 'POST', body: JSON.stringify(payload) }),
  createRescue: (payload) => request('/rescue-requests', { method: 'POST', body: JSON.stringify(payload) }),
  assignRescue: (id, payload) => request(`/rescue-requests/${id}/assign`, { method: 'PATCH', body: JSON.stringify(payload) }),
  updateRescue: (id, payload) => request(`/rescue-requests/${id}/status`, { method: 'PATCH', body: JSON.stringify(payload) }),
  updateHospital: (id, payload) => request(`/hospitals/${id}/capacity`, { method: 'PATCH', body: JSON.stringify(payload) }),
  updateShelter: (id, payload) => request(`/shelters/${id}/capacity`, { method: 'PATCH', body: JSON.stringify(payload) }),
  updateAmbulance: (id, payload) => request(`/ambulances/${id}/status`, { method: 'PATCH', body: JSON.stringify(payload) }),
  createAlert: (payload) => request('/alerts', { method: 'POST', body: JSON.stringify(payload) }),
  acknowledgeAlert: (id, payload = {}) => request(`/alerts/${id}/acknowledge`, { method: 'POST', body: JSON.stringify(payload) }),
  coordination: () => request('/coordination'),
  createDistribution: (payload) => request('/distributions', { method: 'POST', body: JSON.stringify(payload) }),
  createVolunteerAssignment: (payload) => request('/volunteer-assignments', { method: 'POST', body: JSON.stringify(payload) }),
  nationalAlerts: () => request('/national-alerts'),
  createNewsUpdate: (payload) => request('/news-updates', { method: 'POST', body: JSON.stringify(payload) }),
  createWelfareCheck: (payload) => request('/welfare-checks', { method: 'POST', body: JSON.stringify(payload) }),
  updateWelfareCheck: (id, payload) => request(`/welfare-checks/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  createSupplyRequest: (payload) => request('/supply-requests', { method: 'POST', body: JSON.stringify(payload) }),
  updateSupplyRequest: (id, payload) => request(`/supply-requests/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  acknowledgeHospitalNotification: (id) => request(`/hospital-notifications/${id}/acknowledge`, { method: 'PATCH', body: '{}' }),
  createDonation: (payload) => request('/donations', { method: 'POST', body: JSON.stringify(payload) }),
  shareLocation: (payload) => request('/location-pings', { method: 'POST', body: JSON.stringify(payload) }),
  autoDispatch: (id) => request(`/rescue-requests/${id}/auto-dispatch`, { method: 'POST', body: '{}' }),
  safeRoute: ({ latitude, longitude, destination = 'shelter' }) =>
    request(`/safe-route?latitude=${encodeURIComponent(latitude)}&longitude=${encodeURIComponent(longitude)}&destination=${encodeURIComponent(destination)}`),
};

export function isNetworkFailure(error) {
  return error instanceof TypeError || !error?.status;
}
