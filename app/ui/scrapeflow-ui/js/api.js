(function () {
  const cfg = window.ScrapeFlowConfig;
  function useMock() { return cfg.USE_MOCK; }
  function setMockMode(value) { cfg.USE_MOCK = !!value; localStorage.setItem("sf_use_mock", String(!!value)); }
  function request(path, options = {}) { return fetch(`${cfg.API_BASE_URL}${path}`, { headers: { "Content-Type": "application/json", ...(options.headers || {}) }, ...options }).then(async (response) => { const payload = await response.json().catch(() => ({})); if (!response.ok || payload.success === false) throw new Error(payload.message || payload.detail || `Request failed: ${response.status}`); return payload.data; }); }
  async function withFallback(realCall, mockCall) { if (useMock()) return mockCall(); try { return await realCall(); } catch (error) { console.warn("API falling back to mock mode", error); setMockMode(true); return mockCall(); } }
  window.ScrapeFlowAPI = {
    useMock, setMockMode,
    createUser: (payload) => withFallback(() => request("/users", { method: "POST", body: JSON.stringify(payload) }), () => window.ScrapeFlowMock.createUser(payload)),
    login: ({ email, password }) => withFallback(() => Promise.resolve({ email, password, name: email.split("@")[0], id: `local_${Date.now()}` }), () => window.ScrapeFlowMock.login(email, password)),
    createProject: (payload) => withFallback(() => request("/projects", { method: "POST", body: JSON.stringify(payload) }), () => window.ScrapeFlowMock.createProject(payload)),
    getProjects: (userId) => withFallback(() => request(`/users/${userId}/projects`), () => window.ScrapeFlowMock.getProjects(userId)),
    getProject: (projectId) => withFallback(() => request(`/projects/${projectId}`), () => window.ScrapeFlowMock.getProject(projectId)),
    createConversation: (payload) => withFallback(() => request("/conversations", { method: "POST", body: JSON.stringify(payload) }), () => window.ScrapeFlowMock.createConversation(payload)),
    getConversation: (conversationId) => withFallback(() => request(`/conversations/${conversationId}`), () => window.ScrapeFlowMock.getConversation(conversationId)),
    getProjectConversations: (projectId) => withFallback(() => request(`/projects/${projectId}/conversations`), () => window.ScrapeFlowMock.getProjectConversations(projectId)),
    sendMessage: (conversationId, payload) => withFallback(() => request(`/conversations/${conversationId}/messages`, { method: "POST", body: JSON.stringify(payload) }), () => window.ScrapeFlowMock.sendMessage(conversationId, payload)),
    getMessages: (conversationId) => withFallback(() => request(`/conversations/${conversationId}/messages`), () => window.ScrapeFlowMock.getMessages(conversationId)),
    getProjectContext: (projectId) => withFallback(() => request(`/projects/${projectId}/context`), () => window.ScrapeFlowMock.getProjectContext(projectId)),
    updateProjectContext: (projectId, payload) => withFallback(() => request(`/projects/${projectId}/context`, { method: "PATCH", body: JSON.stringify(payload) }), () => window.ScrapeFlowMock.updateProjectContext(projectId, payload)),
    getJobs: (projectId) => withFallback(() => request(`/projects/${projectId}/jobs`), () => window.ScrapeFlowMock.getJobs(projectId)),
    createJob: (payload) => withFallback(() => request("/jobs", { method: "POST", body: JSON.stringify(payload) }), () => window.ScrapeFlowMock.createJob(payload)),
    updateJob: (jobId, payload) => withFallback(() => request(`/jobs/${jobId}`, { method: "PATCH", body: JSON.stringify(payload) }), () => window.ScrapeFlowMock.updateJob(jobId, payload)),
    getResults: () => withFallback(() => Promise.reject(new Error("Results API unavailable")), () => window.ScrapeFlowMock.getResults()),
    getExports: () => withFallback(() => Promise.reject(new Error("Exports API unavailable")), () => window.ScrapeFlowMock.getExports()),
  };
})();
