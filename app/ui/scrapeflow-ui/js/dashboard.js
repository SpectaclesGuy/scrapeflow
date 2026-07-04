(function () {
  const ui = window.ScrapeFlowUI;
  document.addEventListener('DOMContentLoaded', () => {
    const main = ui.shell('dashboard', 'Dashboard', 'A compact view of active work across projects and jobs.');
    if (!main || !ui.requireAuth()) return;
    const session = ui.currentSession();
    main.innerHTML = `
      <section class="metric-grid"></section>
      <section class="panel-grid compact-panel-grid">
        <div class="card">
          <div class="card-header"><p class="eyebrow">Projects</p><h2 style="margin:0;font-size:20px">Recent workspaces</h2></div>
          <div class="card-body"><div id="recentProjects" class="list"></div></div>
        </div>
        <div class="card">
          <div class="card-header"><p class="eyebrow">Jobs</p><h2 style="margin:0;font-size:20px">Latest runs</h2></div>
          <div class="card-body"><div id="recentJobs" class="list"></div></div>
        </div>
      </section>
      <section class="card compact-hero">
        <div class="card-body compact-hero-body">
          <div>
            <p class="eyebrow">Workspace</p>
            <h2 class="compact-hero-title">${session.name}, you can move from planning to execution from one place.</h2>
          </div>
          <div class="quick-actions compact-quick-actions">
            <a class="button" href="/projects.html">New project</a>
            <a class="button-secondary" href="/chat.html">Open chat</a>
            <a class="button-secondary" href="/jobs.html">View jobs</a>
          </div>
        </div>
      </section>`;

    window.ScrapeFlowAPI.getProjects(session.id).then(async (projects) => {
      const jobs = (await Promise.all(projects.map((project) => window.ScrapeFlowAPI.getJobs(project.id)))).flat();
      const stats = [
        ['Projects', projects.length],
        ['Running', jobs.filter((job) => job.status === 'running').length],
        ['Completed', jobs.filter((job) => job.status === 'completed').length],
        ['Failed', jobs.filter((job) => job.status === 'failed').length],
      ];
      main.querySelector('.metric-grid').innerHTML = stats.map(([label, value]) => `<div class="card stat-card compact-stat-card"><span class="stat-label">${label}</span><span class="stat-value">${value}</span></div>`).join('');
      ui.renderList(main.querySelector('#recentProjects'), projects.slice(0, 4), (project) => `<div class="list-item"><div><div style="font-weight:700">${project.name}</div><div class="inline-meta"><span>${project.description || 'No description'}</span></div></div><a class="button-secondary" href="/project.html?project=${project.id}" data-project="${project.id}">Open</a></div>`, 'No projects yet.');
      ui.renderList(main.querySelector('#recentJobs'), jobs.slice(0, 4), (job) => `<div class="list-item"><div><div style="font-weight:700">${job.job_type}</div><div class="inline-meta"><span>${ui.formatDate(job.updated_at)}</span></div></div><span class="${ui.statusClass(job.status)}">${job.status}</span></div>`, 'No jobs yet.');
      main.querySelectorAll('[data-project]').forEach((link) => link.addEventListener('click', () => ui.setActiveProject(projects.find((item) => item.id === link.dataset.project))));
    }).catch((error) => {
      main.querySelector('.metric-grid').innerHTML = `<div class="error-state">${error.message}</div>`;
      ui.toast(error.message, 'error');
    });
  });
})();
