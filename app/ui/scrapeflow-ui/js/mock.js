(function () {
  const seedProjects = [
    { id: "proj_demo_1", user_id: "user_demo", name: "Review Harvest", description: "Pull verified review records from major marketplaces.", status: "active", created_at: new Date().toISOString(), updated_at: new Date().toISOString(), domain: "trustpilot.com", job_count: 3 },
    { id: "proj_demo_2", user_id: "user_demo", name: "Catalog Extractor", description: "Capture laptop pricing, rating, and stock details.", status: "active", created_at: new Date().toISOString(), updated_at: new Date().toISOString(), domain: "example.com", job_count: 2 },
  ];
  const seedMessages = [{ id: "msg_demo_1", conversation_id: "conv_demo_1", role: "assistant", content: "I can turn your request into a browser extraction plan. Add a target URL and the fields you need.", created_at: new Date().toISOString() }];
  const seedJobs = [
    { id: "job_demo_1", project_id: "proj_demo_1", status: "running", job_type: "extraction", created_at: new Date().toISOString(), updated_at: new Date().toISOString(), config: { pages: 18, records: 72 }, result_location: null, error_message: null },
    { id: "job_demo_2", project_id: "proj_demo_2", status: "completed", job_type: "extraction", created_at: new Date().toISOString(), updated_at: new Date().toISOString(), config: { pages: 8, records: 164 }, result_location: "exports/catalog.xlsx", error_message: null },
  ];
  const seedContext = { id: "ctx_demo_1", project_id: "proj_demo_1", target_url: "https://trustpilot.com", domain: "trustpilot.com", entity: "reviews", fields: ["rating", "verified", "content", "date"], filters: ["verified only"], pagination: { type: "offset", pages: 10 }, auth_required: false, export_format: "json", schedule: { cadence: "manual" }, current_plan: { steps: ["Open page", "Paginate", "Extract review cards", "Validate schema"] }, current_schema: { rating: "int", verified: "boolean", content: "text", date: "datetime" }, summary: "Review extraction plan configured and ready to run.", status: "draft", version: 3, created_at: new Date().toISOString(), updated_at: new Date().toISOString() };
  const seedResults = Array.from({ length: 8 }).map((_, idx) => ({ id: `res_${idx + 1}`, project: "Review Harvest", source: "trustpilot.com", title: `Sample review ${idx + 1}`, rating: 5 - (idx % 3), verified: idx % 2 === 0, status: idx % 4 === 0 ? "warning" : "valid", evidence: `div.review-card:nth-child(${idx + 1})` }));
  const seedExports = [{ id: "exp_1", name: "review-harvest.json", format: "JSON", created_at: new Date().toISOString(), size: "1.8 MB" }, { id: "exp_2", name: "review-harvest.csv", format: "CSV", created_at: new Date().toISOString(), size: "842 KB" }];
  const db = { users: [], authUsers: [], projects: seedProjects, conversations: [{ id: "conv_demo_1", project_id: "proj_demo_1", user_id: "user_demo", title: "Discovery chat", status: "active", created_at: new Date().toISOString(), updated_at: new Date().toISOString() }], messages: seedMessages, jobs: seedJobs, contexts: [seedContext], results: seedResults, exports: seedExports };
  function clone(value) { return JSON.parse(JSON.stringify(value)); }
  function stamp() { return new Date().toISOString(); }
  function id(prefix) { return `${prefix}_${Math.random().toString(36).slice(2, 10)}`; }
  function findContext(projectId) { return db.contexts.find((item) => item.project_id === projectId); }
  function inferContextUpdate(content, projectId) {
    const context = findContext(projectId) || clone(seedContext);
    const urlMatch = content.match(/https?:\/\/[^\s]+/i);
    const exportMatch = content.match(/export as (excel|csv|json)/i);
    const fields = [];
    ["price", "rating", "verified", "content", "date", "city", "rent", "area", "contact", "stock"].forEach((field) => { if (content.toLowerCase().includes(field)) fields.push(field); });
    context.target_url = urlMatch ? urlMatch[0] : context.target_url;
    context.domain = urlMatch ? new URL(urlMatch[0]).hostname : context.domain;
    context.export_format = exportMatch ? exportMatch[1].toLowerCase() : context.export_format || "json";
    context.fields = Array.from(new Set([...(context.fields || []), ...fields]));
    if (content.toLowerCase().includes("review")) context.entity = "reviews";
    if (content.toLowerCase().includes("laptop")) context.entity = "laptops";
    if (content.toLowerCase().includes("listing")) context.entity = "listings";
    context.summary = `Latest instruction captured: ${content.slice(0, 110)}`;
    context.version = (context.version || 0) + 1;
    context.updated_at = stamp();
    context.project_id = projectId;
    return context;
  }
  window.ScrapeFlowMock = {
    async login(email) { const auth = db.authUsers.find((user) => user.email === email) || { id: "user_demo", name: email.split("@")[0], email, password: "demo12345" }; if (!db.authUsers.find((user) => user.email === email)) db.authUsers.push(auth); return clone(auth); },
    async createUser(payload) { const user = { id: id("user"), name: payload.name, email: payload.email, password_hash: payload.password_hash || null, role: payload.role || "user", plan: payload.plan || "free", created_at: stamp(), updated_at: stamp() }; db.users.push(user); db.authUsers.push({ id: user.id, name: user.name, email: user.email, password: payload.password || payload.password_hash || "demo12345" }); return clone(user); },
    async createProject(payload) { const project = { id: id("proj"), user_id: payload.user_id, name: payload.name, description: payload.description || "", status: payload.status || "active", domain: payload.domain || "not set", job_count: 0, created_at: stamp(), updated_at: stamp() }; db.projects.unshift(project); const context = clone(seedContext); context.id = id("ctx"); context.project_id = project.id; context.entity = null; context.target_url = null; context.domain = null; context.fields = []; context.filters = []; context.summary = "Project created. Waiting for extraction instructions."; context.version = 1; db.contexts.unshift(context); return clone(project); },
    async getProjects(userId) { return clone(db.projects.filter((item) => item.user_id === userId || userId === "user_demo")); },
    async getProject(projectId) { return clone(db.projects.find((item) => item.id === projectId)); },
    async createConversation(payload) { const conversation = { id: id("conv"), project_id: payload.project_id, user_id: payload.user_id, title: payload.title || "New conversation", status: payload.status || "active", created_at: stamp(), updated_at: stamp() }; db.conversations.unshift(conversation); return clone(conversation); },
    async getConversation(conversationId) { return clone(db.conversations.find((item) => item.id === conversationId)); },
    async getProjectConversations(projectId) { return clone(db.conversations.filter((item) => item.project_id === projectId)); },
    async sendMessage(conversationId, payload) { const conversation = db.conversations.find((item) => item.id === conversationId); const message = { id: id("msg"), conversation_id: conversationId, role: payload.role, content: payload.content, metadata: payload.metadata || null, created_at: stamp() }; db.messages.push(message); const updatedContext = inferContextUpdate(payload.content, conversation.project_id); const existing = findContext(conversation.project_id); if (existing) Object.assign(existing, updatedContext); else db.contexts.push(updatedContext); return { message: clone(message), context: clone(findContext(conversation.project_id)) }; },
    async getMessages(conversationId) { return clone(db.messages.filter((item) => item.conversation_id === conversationId)); },
    async getProjectContext(projectId) { return clone(findContext(projectId)); },
    async updateProjectContext(projectId, payload) { const context = findContext(projectId); Object.assign(context, payload, { version: (context.version || 1) + 1, updated_at: stamp() }); return clone(context); },
    async getJobs(projectId) { return clone(projectId ? db.jobs.filter((item) => item.project_id === projectId) : db.jobs); },
    async createJob(payload) { const job = { id: id("job"), project_id: payload.project_id, conversation_id: payload.conversation_id || null, status: payload.status || "created", job_type: payload.job_type || "extraction", config: payload.config || { records: 0, pages: 0 }, result_location: payload.result_location || null, error_message: null, created_at: stamp(), updated_at: stamp() }; db.jobs.unshift(job); return clone(job); },
    async updateJob(jobId, payload) { const job = db.jobs.find((item) => item.id === jobId); Object.assign(job, payload, { updated_at: stamp() }); return clone(job); },
    async getResults() { return clone(db.results); },
    async getExports() { return clone(db.exports); },
  };
})();
