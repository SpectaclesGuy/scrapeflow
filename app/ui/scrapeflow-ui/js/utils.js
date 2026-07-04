(function () {
  const key = (name) => `${window.ScrapeFlowConfig.STORAGE_PREFIX}${name}`;
  const routes = [
    ['projects', 'projects', 'Projects', 'PR'],
    ['jobs', 'jobs', 'Jobs', 'JB'],
    ['results', 'results', 'Results', 'RS'],
    ['settings', 'settings', 'Settings', 'ST'],
  ];
  const secondaryRoutes = [
    ['chat', 'chat', 'Chat', 'CH'],
    ['context', 'context', 'Context', 'CT'],
    ['plan', 'plan', 'Plan', 'PL'],
    ['exports', 'exports', 'Exports', 'EX'],
  ];

  function save(name, value) { localStorage.setItem(key(name), JSON.stringify(value)); }
  function load(name, fallback = null) { const raw = localStorage.getItem(key(name)); return raw ? JSON.parse(raw) : fallback; }
  function clear(name) { localStorage.removeItem(key(name)); }
  function toast(message, tone = 'info') {
    let region = document.querySelector('.toast-region');
    if (!region) {
      region = document.createElement('div');
      region.className = 'toast-region';
      document.body.appendChild(region);
    }
    const node = document.createElement('div');
    node.className = 'toast';
    node.dataset.tone = tone;
    node.textContent = message;
    region.appendChild(node);
    setTimeout(() => node.remove(), 3200);
  }
  function statusClass(status = 'created') { return `status-badge status-${status.toLowerCase()}`; }

  function shell(page, title, subtitle) {
    const app = document.querySelector('[data-app]');
    if (!app) return null;
    const session = currentSession();
    app.innerHTML = `
      <div class="app-shell compact-shell">
        <aside class="sidebar compact-sidebar">
          <a class="sidebar-logo" href="/chat">
            <div class="logo-mark">SF</div>
            <div>
              <div class="sidebar-brand">ScrapeFlow</div>
              <div class="sidebar-brand-sub">RaioQuantum</div>
            </div>
          </a>
          <nav class="sidebar-nav compact-nav">
            ${routes.map(([id, href, label, icon]) => `<a class="sidebar-link ${id === page ? 'active' : ''}" href="/${href}"><span class="kbd">${icon}</span><span>${label}</span></a>`).join('')}
          </nav>
          <div class="sidebar-section-label">Workspace</div>
          <nav class="sidebar-footer compact-nav">
            ${secondaryRoutes.map(([id, href, label, icon]) => `<a class="sidebar-link ${id === page ? 'active' : ''}" href="/${href}"><span class="kbd">${icon}</span><span>${label}</span></a>`).join('')}
          </nav>
          <div class="sidebar-spacer"></div>
          <div class="sidebar-account">
            <div>
              <div class="sidebar-account-name">${escapeHtml(session?.name || 'Workspace')}</div>
              <div class="sidebar-account-email">${escapeHtml(session?.email || 'No active session')}</div>
            </div>
            <button class="button-ghost compact-logout" type="button" data-logout-link>Sign out</button>
          </div>
        </aside>
        <div class="content-area compact-content-area">
          <header class="topbar compact-topbar">
            <div class="topbar-title compact-title">
              <h1 class="page-title compact-page-title">${title}</h1>
              <p class="page-subtitle compact-page-subtitle">${subtitle}</p>
            </div>
          </header>
          <main class="main-content compact-main-content"></main>
        </div>
      </div>`;

    const logoutLink = app.querySelector('[data-logout-link]');
    if (logoutLink) {
      logoutLink.addEventListener('click', async () => {
        try { await window.ScrapeFlowAPI.logout(); } catch (error) { console.warn('Logout request failed', error); }
        clear('session'); clear('activeProject'); clear('activeConversation');
        toast('Signed out', 'success');
        setTimeout(() => { window.location.href = '/login'; }, 180);
      });
    }
    return app.querySelector('.main-content');
  }

  function requireAuth() {
    if (document.body.dataset.public === 'true') return true;
    const session = load('session');
    if (!session) {
      window.location.href = '/login';
      return false;
    }
    return true;
  }
  function currentSession() { return load('session'); }
  function setSession(session) { save('session', session); }
  function setActiveProject(project) { save('activeProject', project); }
  function getActiveProject() { return load('activeProject'); }
  function setActiveConversation(conversation) { save('activeConversation', conversation); }
  function getActiveConversation() { return load('activeConversation'); }
  function renderList(container, items, renderer, emptyMessage) {
    if (!items || !items.length) { container.innerHTML = `<div class="empty-state">${emptyMessage}</div>`; return; }
    container.innerHTML = items.map(renderer).join('');
  }
  function modal({ title, body, onConfirm, confirmText = 'Confirm', tone = 'default' }) {
    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop';
    backdrop.innerHTML = `<div class="modal"><div class="modal-header"><h3 style="margin:0">${title}</h3></div><div class="modal-body">${body}</div><div class="modal-footer"><button class="button-ghost" type="button" data-close>Cancel</button><button class="${tone === 'danger' ? 'button-danger' : 'button'}" type="button" data-confirm>${confirmText}</button></div></div>`;
    backdrop.querySelector('[data-close]').addEventListener('click', () => backdrop.remove());
    backdrop.addEventListener('click', (event) => { if (event.target === backdrop) backdrop.remove(); });
    backdrop.querySelector('[data-confirm]').addEventListener('click', async () => { if (onConfirm) await onConfirm(backdrop); backdrop.remove(); });
    document.body.appendChild(backdrop);
  }
  function formatDate(value) { return value ? new Date(value).toLocaleString() : '-'; }
  function escapeHtml(value) { return String(value ?? '').replace(/[&<>\"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[char])); }
  window.ScrapeFlowUI = { save, load, clear, toast, shell, requireAuth, currentSession, setSession, setActiveProject, getActiveProject, setActiveConversation, getActiveConversation, renderList, modal, formatDate, escapeHtml, statusClass };
})();
