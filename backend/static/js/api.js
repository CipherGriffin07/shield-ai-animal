/**
 * SHIELD AI — API client
 * Thin wrapper around fetch() for the FastAPI backend. Handles the
 * bearer token, JSON encoding, and consistent error surfacing.
 */
const SHIELD_API = (() => {
  const BASE = '';

  function getTokens() {
    try { return JSON.parse(localStorage.getItem('shield_auth') || 'null'); }
    catch { return null; }
  }

  function setTokens(tokens) {
    localStorage.setItem('shield_auth', JSON.stringify(tokens));
  }

  function clearTokens() {
    localStorage.removeItem('shield_auth');
  }

  function isLoggedIn() {
    return !!getTokens()?.access_token;
  }

  async function request(path, { method = 'GET', body, form, auth = true, headers = {} } = {}) {
    const opts = { method, headers: { ...headers } };

    if (form) {
      opts.body = form; // FormData - browser sets Content-Type with boundary
    } else if (body !== undefined) {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }

    if (auth) {
      const tokens = getTokens();
      if (tokens?.access_token) opts.headers['Authorization'] = `Bearer ${tokens.access_token}`;
    }

    const response = await fetch(BASE + path, opts);

    if (response.status === 204) return null;

    let data = null;
    try { data = await response.json(); } catch { /* no body */ }

    if (!response.ok) {
      const message = data?.detail
        ? (Array.isArray(data.detail) ? data.detail.map(d => d.msg).join(' ') : data.detail)
        : `Request failed (${response.status})`;
      throw new Error(message);
    }
    return data;
  }

  return {
    getTokens, setTokens, clearTokens, isLoggedIn,

    signup: (payload) => request('/api/auth/signup', { method: 'POST', body: payload, auth: false }),
    login: (payload) => request('/api/auth/login', { method: 'POST', body: payload, auth: false }),
    me: () => request('/api/auth/me'),
    forgotPassword: (email) => request('/api/auth/forgot-password', { method: 'POST', body: { email }, auth: false }),

    createReport: (formData) => request('/api/reports', { method: 'POST', form: formData, auth: false }),
    listReports: () => request('/api/reports', { auth: false }),
    getReport: (id) => request(`/api/reports/${id}`, { auth: false }),
    getTimeline: (id) => request(`/api/reports/${id}/timeline`, { auth: false }),

    chat: (message, history) => request('/api/chat', { method: 'POST', body: { message, history }, auth: false }),

    nearbyCases: () => request('/api/volunteers/me/nearby-cases'),
    acceptCase: (id) => request(`/api/volunteers/me/accept/${id}`, { method: 'POST' }),
    myVolunteerProfile: () => request('/api/volunteers/me'),
    updateVolunteerProfile: (payload) => request('/api/volunteers/me', { method: 'PUT', body: payload }),
    updateVolunteerLocation: (lat, lng) => request('/api/volunteers/me/location', { method: 'PUT', body: { latitude: lat, longitude: lng } }),

    myNgoProfile: () => request('/api/ngos/me'),
    updateNgoProfile: (payload) => request('/api/ngos/me', { method: 'PUT', body: payload }),
    ngoIncomingCases: () => request('/api/ngos/me/incoming-cases'),
    ngoClaimCase: (id) => request(`/api/ngos/me/claim/${id}`, { method: 'POST' }),

    updateStatus: (id, payload) => request(`/api/reports/${id}/status`, { method: 'PATCH', body: payload }),
    medicalReportUrl: (id) => `/api/reports/${id}/medical-report.pdf`,

    listLostFound: (postType) => request(`/api/lost-found${postType ? `?post_type=${postType}` : ''}`, { auth: false }),
    createLostFound: (formData) => request('/api/lost-found', { method: 'POST', form: formData }),
    lostFoundMatches: (id) => request(`/api/lost-found/${id}/matches`, { auth: false }),

    adoptionListings: () => request('/api/adoption/listings', { auth: false }),
    applyAdoption: (payload) => request('/api/adoption/applications', { method: 'POST', body: payload }),

    analyticsSummary: () => request('/api/admin/analytics/summary'),
    analyticsTimeseries: (days = 30) => request(`/api/admin/analytics/timeseries?days=${days}`),
    adminUsers: (role) => request(`/api/admin/users${role ? `?role=${role}` : ''}`),
    deactivateUser: (id) => request(`/api/admin/users/${id}/deactivate`, { method: 'PATCH' }),
    reactivateUser: (id) => request(`/api/admin/users/${id}/reactivate`, { method: 'PATCH' }),

    updateProfile: (payload) => request('/api/users/me', { method: 'PATCH', body: payload }),
    updatePreferences: (payload) => request('/api/users/me/preferences', { method: 'PATCH', body: payload }),
    changePassword: (payload) => request('/api/auth/change-password', { method: 'POST', body: payload }),
  };
})();

function requireAuth(redirectTo = '/login') {
  if (!SHIELD_API.isLoggedIn()) window.location.href = redirectTo;
}

function logout() {
  SHIELD_API.clearTokens();
  window.location.href = '/login';
}
