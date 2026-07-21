const DEFAULT_API_BASE_URL = import.meta.env.PROD ? '/api/v1' : 'http://localhost:5000/api/v1';
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/$/, '');

function readCookie(name) {
  const prefix = `${encodeURIComponent(name)}=`;
  const item = document.cookie.split('; ').find((entry) => entry.startsWith(prefix));
  return item ? decodeURIComponent(item.slice(prefix.length)) : '';
}

async function request(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const csrfToken = !['GET', 'HEAD', 'OPTIONS'].includes(method) ? readCookie('resq_csrf') : '';
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
      ...options.headers,
    },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.error || `Request failed with status ${response.status}`);
    error.status = response.status;
    error.requestId = body.request_id || response.headers.get('X-Request-ID');
    if (response.status === 401 && !path.startsWith('/auth/')) {
      window.dispatchEvent(new CustomEvent('resq:session-expired'));
    }
    throw error;
  }
  return body;
}

export function openDemoSession(role) {
  return request('/auth/demo-session', { method: 'POST', body: JSON.stringify({ role }) });
}

export function login(payload) {
  return request('/auth/login', { method: 'POST', body: JSON.stringify(payload) });
}

export function completeMfaLogin(payload) {
  return request('/auth/mfa/challenge', { method: 'POST', body: JSON.stringify(payload) });
}

export function register(payload) {
  return request('/auth/register', { method: 'POST', body: JSON.stringify(payload) });
}

export function restoreSession() {
  return request('/auth/me');
}

export function logout() {
  return request('/auth/logout', { method: 'POST', body: '{}' });
}

export function changePassword(payload) {
  return request('/auth/change-password', { method: 'POST', body: JSON.stringify(payload) });
}

export function getMfaStatus() {
  return request('/auth/mfa/status');
}

export function beginMfaSetup(payload) {
  return request('/auth/mfa/setup', { method: 'POST', body: JSON.stringify(payload) });
}

export function confirmMfaSetup(payload) {
  return request('/auth/mfa/confirm', { method: 'POST', body: JSON.stringify(payload) });
}

export function regenerateMfaRecoveryCodes(payload) {
  return request('/auth/mfa/recovery-codes', { method: 'POST', body: JSON.stringify(payload) });
}

export function disableMfa(payload) {
  return request('/auth/mfa/disable', { method: 'POST', body: JSON.stringify(payload) });
}

export const api = {
  bootstrap: () => request('/operations/bootstrap'),
  adminUsers: () => request('/admin/users'),
  provisionUser: (payload) => request('/admin/users', { method: 'POST', body: JSON.stringify(payload) }),
  updateUserAccess: (id, payload) => request(`/admin/users/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  resetUserPassword: (id, payload) => request(`/admin/users/${id}/reset-password`, { method: 'POST', body: JSON.stringify(payload) }),
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
