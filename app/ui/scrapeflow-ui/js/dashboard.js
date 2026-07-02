(function () {
  const ui = window.ScrapeFlowUI;
  document.addEventListener("DOMContentLoaded", () => {
    const main = ui.shell("dashboard", "Operations dashboard", "Monitor project velocity, planner output, and extraction jobs from a single command surface.");
    if (!main || !ui.requireAuth()) return;
    const session = ui.currentSession();
    main.innerHTML = `<section class="metric-grid"></section><section class="panel-grid"><div class="card"><div class="card-header"><p class="eyebrow">Recent projects</p><h2 style="margin:0;font-size:22px">Active workspaces</h2></div><div class="card-body"><div id="recentProjects" class="list"></div></div></div><div class="card"><div class="card-header"><p class="eyebrow">Quick actions</p><h2 style="margin:0;font-size:22px">Move the workflow forward</h2></div><div class="card-body"><div class="quick-actions"><a class="button" href="/projects.html">New project</a><a class="button-secondary" href="/chat.html">Open chat</a><a class="button-secondary" href="/jobs.html">Run job</a></div><div id="recentJobs" class="list" style="margin-top:18px"></div></div></div></section><section class="card hero-card"><div class="hero-grid"><div><p class="eyebrow">Operational posture</p><h2 class="hero-title" style="font-size:48px">${session.name}, your extraction stack is ready for live runs.</h2><p class="hero-copy">Use the dashboard to keep planning, context review, execution, and export decisions in sync across the team.</p></div><div class="hero-visual"><div class="hero-terminal"><div class="window-dots"><span></span><span></span><span></span></div><pre>{
  "planner": "active",
  "browserAutomation": true,
  "contextVersion": 3,
  "validation": "schema + evidence",
  "nextStep": "Review plan and queue extraction"
}</pre></div></div></div></section>`;
    window.ScrapeFlowAPI.getProjects(session.id).then(async (projects) => {
      const jobs = (await Promise.all(projects.map((project) => window.ScrapeFlowAPI.getJobs(project.id)))).flat();
      const stats = [["Total Projects", projects.length, "Across active workspace(s)"],["Running Jobs", jobs.filter((job) => job.status === "running").length, "Currently extracting"],["Completed Jobs", jobs.filter((job) => job.status === "completed").length, "Ready for review"],["Failed Jobs", jobs.filter((job) => job.status === "failed").length, "Need retry or fix"]];
      main.querySelector(".metric-grid").innerHTML = stats.map(([label, value, meta]) => `<div class="card stat-card"><span class="stat-label">${label}</span><span class="stat-value">${value}</span><span class="stat-meta">${meta}</span></div>`).join("");
      ui.renderList(main.querySelector("#recentProjects"), projects.slice(0, 4), (project) => `<div class="list-item"><div><div style="font-weight:700">${project.name}</div><div class="inline-meta"><span>${project.description || "No description"}</span><span>${project.status}</span></div></div><a class="button-secondary" href="/project.html?project=${project.id}" data-project="${project.id}">Open</a></div>`, "No projects yet.");
      ui.renderList(main.querySelector("#recentJobs"), jobs.slice(0, 4), (job) => `<div class="list-item"><div><div style="font-weight:700">${job.id}</div><div class="inline-meta"><span>${job.job_type}</span><span>${ui.formatDate(job.updated_at)}</span></div></div><span class="${ui.statusClass(job.status)}">${job.status}</span></div>`, "No jobs yet.");
      main.querySelectorAll("[data-project]").forEach((link) => link.addEventListener("click", () => ui.setActiveProject(projects.find((item) => item.id === link.dataset.project))));
    }).catch((error) => { main.querySelector(".metric-grid").innerHTML = `<div class="error-state">${error.message}</div>`; ui.toast(error.message, "error"); });
  });
})();
