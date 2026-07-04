(function () {
  const cfg = window.ScrapeFlowConfig;

  function useMock() { return cfg.USE_MOCK; }
  function setMockMode(value) {
    cfg.USE_MOCK = !!value;
    localStorage.setItem('sf_use_mock', String(!!value));
  }

  async function request(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }
    const response = await fetch(`${cfg.API_BASE_URL}${path}`, {
      credentials: 'same-origin',
      headers,
      ...options,
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload.success === false) {
      throw new Error(payload.message || payload.detail || `Request failed: ${response.status}`);
    }
    return payload.data;
  }

  async function withFallback(realCall, mockCall) {
    if (useMock()) return mockCall();
    try {
      return await realCall();
    } catch (error) {
      console.warn('API falling back to mock mode', error);
      setMockMode(true);
      return mockCall();
    }
  }

  window.ScrapeFlowAPI = {
    useMock,
    setMockMode,
    signup: (payload) => request('/auth/signup', { method: 'POST', body: JSON.stringify(payload) }),
    login: (payload) => request('/auth/login', { method: 'POST', body: JSON.stringify(payload) }),
    logout: () => request('/auth/logout', { method: 'POST' }),
    getSession: () => request('/auth/me'),
    beginGoogleLogin: () => { window.location.href = `${cfg.API_BASE_URL}/auth/google/login`; },
    createUser: (payload) => request('/users', { method: 'POST', body: JSON.stringify(payload) }),
    createProject: (payload) => request('/projects', { method: 'POST', body: JSON.stringify(payload) }),
    getProjects: (userId) => request(`/users/${userId}/projects`),
    getProject: (projectId) => request(`/projects/${projectId}`),
    createConversation: (payload) => request('/conversations', { method: 'POST', body: JSON.stringify(payload) }),
    getConversation: (conversationId) => request(`/conversations/${conversationId}`),
    getProjectConversations: (projectId) => request(`/projects/${projectId}/conversations`),
    sendMessage: (conversationId, payload) => request(`/conversations/${conversationId}/messages`, { method: 'POST', body: JSON.stringify(payload) }),
    getMessages: (conversationId) => request(`/conversations/${conversationId}/messages`),
    getProjectContext: (projectId) => request(`/projects/${projectId}/context`),
    updateProjectContext: (projectId, payload) => request(`/projects/${projectId}/context`, { method: 'PATCH', body: JSON.stringify(payload) }),
    getJobs: (projectId) => request(`/projects/${projectId}/jobs`),
    createJob: (payload) => request('/jobs', { method: 'POST', body: JSON.stringify(payload) }),
    startJob: (jobId) => request(`/jobs/${jobId}/start`, { method: 'POST' }),
    runJob: (jobId) => request(`/jobs/${jobId}/run`, { method: 'POST' }),
    getJob: (jobId) => request(`/jobs/${jobId}`),
    updateJob: (jobId, payload) => request(`/jobs/${jobId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    getJobResults: (jobId) => request(`/jobs/${jobId}/results`),
    getResults: () => withFallback(() => Promise.reject(new Error('Results API unavailable')), () => window.ScrapeFlowMock.getResults()),
    getExports: () => withFallback(() => Promise.reject(new Error('Exports API unavailable')), () => window.ScrapeFlowMock.getExports()),
  };
})();
