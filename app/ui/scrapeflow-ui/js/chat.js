(function () {
  const ui = window.ScrapeFlowUI;
  const api = window.ScrapeFlowAPI;

  let projects = [];
  let conversations = [];
  let messages = [];
  let currentProject = null;
  let currentConversation = null;
  let currentContext = null;
  let activeJob = null;
  let activeResults = [];
  let pollHandle = null;

  document.addEventListener('DOMContentLoaded', async () => {
    if (!ui.requireAuth()) return;
    renderWorkspaceShell();
    await bootstrap();
  });

  async function bootstrap() {
    const session = ui.currentSession();
    projects = await api.getProjects(session.id);
    const params = new URLSearchParams(window.location.search);
    const requestedProjectId = params.get('project') || ui.getActiveProject()?.id || projects[0]?.id;
    if (requestedProjectId) {
      await selectProject(requestedProjectId);
    } else {
      renderWorkspace();
    }
  }

  function renderWorkspaceShell() {
    const app = document.querySelector('[data-app]');
    const session = ui.currentSession();
    app.innerHTML = `
      <div class="workspace-shell">
        <aside class="workspace-sidebar">
          <div class="workspace-brand-row">
            <div class="logo-mark">SF</div>
            <div><div class="workspace-brand">ScrapeFlow</div><div class="workspace-company">RaioQuantum</div></div>
          </div>
          <div class="workspace-section">
            <div class="workspace-section-head"><span>Projects</span><button class="button-ghost tiny-button" id="newProjectBtn" type="button">New</button></div>
            <div id="projectHistory" class="workspace-history"></div>
          </div>
          <div class="workspace-section">
            <div class="workspace-section-head"><span>Chats</span><button class="button-ghost tiny-button" id="newChatBtn" type="button">New</button></div>
            <div id="conversationHistory" class="workspace-history"></div>
          </div>
          <div class="workspace-sidebar-footer">
            <div class="workspace-user">${ui.escapeHtml(session.name)}</div>
            <div class="workspace-user-sub">${ui.escapeHtml(session.email)}</div>
            <div class="workspace-footer-actions"><a class="button-ghost tiny-button" href="/settings">Settings</a><button class="button-ghost tiny-button" id="logoutBtn" type="button">Sign out</button></div>
          </div>
        </aside>
        <main class="workspace-main">
          <section class="workspace-thread-panel">
            <div id="threadHeader" class="workspace-thread-header"></div>
            <div id="chatThread" class="workspace-thread"></div>
            <div class="workspace-composer-wrap"><form id="chatComposer" class="workspace-composer"><textarea id="chatInput" placeholder="What's on your mind?"></textarea><button class="button workspace-send" type="submit">Send</button></form></div>
          </section>
          <aside class="workspace-live-panel">
            <div class="workspace-live-card"><div class="workspace-live-head">Live run</div><div id="jobStatusPanel" class="workspace-live-body"></div></div>
            <div class="workspace-live-card"><div class="workspace-live-head">Context</div><div id="contextPanel" class="workspace-live-body"></div></div>
          </aside>
        </main>
      </div>`;
    document.getElementById('logoutBtn').addEventListener('click', async () => {
      try { await api.logout(); } catch (error) { console.warn(error); }
      ui.clear('session'); ui.clear('activeProject'); ui.clear('activeConversation'); window.location.href = '/login';
    });
    document.getElementById('newProjectBtn').addEventListener('click', () => createProjectFromPrompt());
    document.getElementById('newChatBtn').addEventListener('click', () => createFreshConversation());
    document.getElementById('chatComposer').addEventListener('submit', handlePromptSubmit);
  }

  async function selectProject(projectId) {
    currentProject = projects.find((item) => item.id === projectId) || await api.getProject(projectId);
    ui.setActiveProject(currentProject);
    conversations = await api.getProjectConversations(projectId);
    currentConversation = conversations.at(-1) || null;
    messages = currentConversation ? await api.getMessages(currentConversation.id) : [];
    if (currentConversation) ui.setActiveConversation(currentConversation);
    currentContext = await api.getProjectContext(projectId);
    activeJob = null;
    activeResults = [];
    renderWorkspace();
  }

  async function createFreshConversation() {
    if (!currentProject) return;
    const session = ui.currentSession();
    const conversation = await api.createConversation({ project_id: currentProject.id, user_id: session.id, title: 'New extraction' });
    conversations.push(conversation);
    currentConversation = conversation;
    ui.setActiveConversation(conversation);
    messages = [];
    renderWorkspace();
  }

  async function createProjectFromPrompt(seedPrompt = '') {
    const session = ui.currentSession();
    const project = await api.createProject({ user_id: session.id, name: inferProjectName(seedPrompt), description: seedPrompt || 'Extraction workspace' });
    projects.unshift(project);
    await selectProject(project.id);
  }

  function inferProjectName(prompt) {
    const urlMatch = prompt.match(/https?:\/\/([^/\s]+)/i);
    if (urlMatch) return `Extract ${urlMatch[1]}`;
    const words = prompt.trim().split(/\s+/).filter(Boolean).slice(0, 4);
    return words.length ? words.map((word) => word[0].toUpperCase() + word.slice(1)).join(' ') : 'New project';
  }

  async function handlePromptSubmit(event) {
    event.preventDefault();
    const input = document.getElementById('chatInput');
    const content = input.value.trim();
    if (!content) return;
    if (!currentProject) await createProjectFromPrompt(content);
    if (!currentConversation) await createFreshConversation();

    const payload = await api.sendMessage(currentConversation.id, { role: 'user', content });
    messages.push(payload.message);
    currentContext = payload.context;
    input.value = '';
    renderWorkspace();

    const questions = clarificationQuestions(currentContext);
    if (questions.length) {
      const assistant = await api.sendMessage(currentConversation.id, { role: 'assistant', content: questions.join('\n') });
      messages.push(assistant.message);
      renderWorkspace();
      return;
    }

    const startNotice = await api.sendMessage(currentConversation.id, { role: 'assistant', content: 'Starting extraction now. I will keep the live run status visible here.' });
    messages.push(startNotice.message);
    renderWorkspace();

    const jobConfig = buildJobConfigFromContext(currentContext, currentProject.id);
    const job = await api.createJob({ project_id: currentProject.id, conversation_id: currentConversation.id, status: 'queued', job_type: 'extraction', config: jobConfig });
    activeJob = await api.startJob(job.id);
    pollJob(job.id);
    renderWorkspace();
  }

  function clarificationQuestions(context) {
    const questions = [];
    if (!context?.target_url) questions.push('What is the target URL?');
    if (!context?.fields?.length) questions.push('Which fields should I extract?');
    return questions;
  }

  function buildJobConfigFromContext(context, projectId) {
    const fields = (context.fields || []).map((field) => {
      const lowered = String(field).toLowerCase();
      let selector = `[class*="${lowered}"], [id*="${lowered}"]`;
      let type = 'text';
      if (lowered.includes('price')) selector = '.price, .product-price, .a-price .a-offscreen, .a-price-whole, .wrong-price-class, [class*="price"]';
      else if (lowered.includes('rating')) selector = '.rating, .a-icon-alt, [class*="rating"], [aria-label*="rating"]';
      else if (lowered.includes('title') || lowered.includes('name')) selector = 'h1, h2, h3, .product-title, .title, .name, [data-cy="title-recipe"], .a-size-base-plus';
      else if (lowered.includes('image') || lowered.includes('logo') || lowered.includes('photo')) { selector = 'img'; type = 'src'; }
      else if (lowered.includes('url') || lowered.includes('link')) { selector = 'a'; type = 'href'; }
      return { name: field, selector, type, required: true };
    });
    return {
      job_id: null,
      project_id: projectId,
      target_url: context.target_url,
      mode: 'auto',
      entity: context.entity || 'record',
      container_selector: '[data-component-type="s-search-result"], .s-result-item, [data-asin], .product-card, .product, .product-item, article, li, .item, .card, tr',
      fields,
      pagination: { enabled: false, type: 'none', max_pages: 1 },
      browser: { headless: true, wait_until: 'load', timeout: 45000 },
      slm: { enabled: true, provider: 'gemini', model: 'gemini-3.5-flash', max_input_chars: 12000 },
      output: { formats: ['json', 'csv'], include_evidence: true },
    };
  }

  function pollJob(jobId) {
    if (pollHandle) clearInterval(pollHandle);
    const tick = async () => {
      activeJob = await api.getJob(jobId);
      if (activeJob.status === 'completed' || activeJob.status === 'failed') {
        if (activeJob.status === 'completed') {
          const results = await api.getJobResults(jobId);
          activeResults = results.records || [];
        }
        messages = await api.getMessages(currentConversation.id);
        clearInterval(pollHandle);
        pollHandle = null;
      }
      renderWorkspace();
    };
    tick();
    pollHandle = setInterval(tick, 2000);
  }

  function renderWorkspace() { renderProjectHistory(); renderConversationHistory(); renderHeader(); renderMessages(); renderContext(); renderJobStatus(); }
  function renderProjectHistory() {
    const node = document.getElementById('projectHistory'); if (!node) return;
    node.innerHTML = projects.length ? projects.map((project) => `<button class="history-item ${currentProject?.id === project.id ? 'active' : ''}" data-project="${project.id}"><span class="history-title">${ui.escapeHtml(project.name)}</span><span class="history-meta">${ui.formatDate(project.updated_at)}</span></button>`).join('') : '<div class="empty-mini">No projects yet</div>';
    node.querySelectorAll('[data-project]').forEach((button) => button.addEventListener('click', () => selectProject(button.dataset.project)));
  }
  function renderConversationHistory() {
    const node = document.getElementById('conversationHistory'); if (!node) return;
    node.innerHTML = conversations.length ? conversations.map((conversation) => `<button class="history-item ${currentConversation?.id === conversation.id ? 'active' : ''}" data-conversation="${conversation.id}"><span class="history-title">${ui.escapeHtml(conversation.title || 'Conversation')}</span><span class="history-meta">${ui.formatDate(conversation.created_at)}</span></button>`).join('') : '<div class="empty-mini">No chats yet</div>';
    node.querySelectorAll('[data-conversation]').forEach((button) => button.addEventListener('click', async () => { currentConversation = conversations.find((item) => item.id === button.dataset.conversation); ui.setActiveConversation(currentConversation); messages = await api.getMessages(currentConversation.id); renderWorkspace(); }));
  }
  function renderHeader() {
    const node = document.getElementById('threadHeader'); if (!node) return;
    node.innerHTML = `<div><div class="workspace-thread-title">${ui.escapeHtml(currentProject?.name || 'New workspace')}</div><div class="workspace-thread-sub">${currentContext?.target_url || 'Describe an extraction job to begin.'}</div></div><div class="workspace-thread-actions"><a class="button-ghost tiny-button" href="/projects">Projects</a><a class="button-ghost tiny-button" href="/jobs">Jobs</a></div>`;
  }
  function renderMessages() {
    const node = document.getElementById('chatThread'); if (!node) return;
    node.innerHTML = messages.length ? messages.map((message) => `<article class="workspace-message ${message.role === 'user' ? 'user' : 'assistant'}"><div class="workspace-message-meta">${message.role} · ${ui.formatDate(message.created_at)}</div><div class="workspace-message-content">${ui.escapeHtml(message.content).replace(/\n/g, '<br>')}</div></article>`).join('') : '<div class="workspace-empty">Start with a URL and the fields you want to extract.</div>';
    node.scrollTop = node.scrollHeight;
  }
  function renderContext() {
    const node = document.getElementById('contextPanel'); if (!node) return;
    node.innerHTML = `<div class="mini-stat"><span>URL</span><strong>${ui.escapeHtml(currentContext?.target_url || 'Pending')}</strong></div><div class="mini-stat"><span>Entity</span><strong>${ui.escapeHtml(currentContext?.entity || 'Pending')}</strong></div><div class="mini-stat"><span>Fields</span><strong>${ui.escapeHtml((currentContext?.fields || []).join(', ') || 'Pending')}</strong></div><div class="mini-stat"><span>Version</span><strong>v${currentContext?.version || 0}</strong></div>`;
  }
  function renderJobStatus() {
    const node = document.getElementById('jobStatusPanel'); if (!node) return;
    if (!activeJob) { node.innerHTML = '<div class="workspace-empty">No live run yet.</div>'; return; }
    node.innerHTML = `<div class="mini-stat"><span>Status</span><strong>${ui.escapeHtml(activeJob.status)}</strong></div><div class="mini-stat"><span>Progress</span><strong>${activeJob.progress || 0}%</strong></div><div class="mini-stat"><span>Pages</span><strong>${activeJob.pages_processed || 0}</strong></div><div class="mini-stat"><span>Records</span><strong>${activeJob.records_found || 0}</strong></div><div class="mini-stat"><span>Updated</span><strong>${ui.formatDate(activeJob.updated_at)}</strong></div>${activeJob.error_message ? `<div class="workspace-error">${ui.escapeHtml(activeJob.error_message)}</div>` : ''}${activeResults.length ? `<pre class="workspace-preview">${ui.escapeHtml(JSON.stringify(activeResults.slice(0, 2), null, 2))}</pre>` : ''}`;
  }
})();
