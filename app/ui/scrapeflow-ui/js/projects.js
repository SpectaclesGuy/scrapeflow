(function () {
  const ui = window.ScrapeFlowUI;
  const api = window.ScrapeFlowAPI;
  function projectCard(project) { return `<article class="card project-card"><div class="project-card-header"><div><div class="project-card-title">${project.name}</div><div class="inline-meta"><span>${project.status}</span><span>${ui.formatDate(project.updated_at)}</span></div></div><span class="status-badge status-${project.status}">${project.status}</span></div><p class="project-card-copy">${project.description || "No description yet. Start the chat workflow to define extraction goals."}</p><div class="inline-meta"><span>Domain: ${project.domain || "pending"}</span><span>Jobs: ${project.job_count || 0}</span></div><div class="quick-actions"><a class="button-secondary" href="/project.html?project=${project.id}" data-open="${project.id}">Open</a><button class="button-ghost" data-rename="${project.id}">Rename</button><button class="button-danger" data-delete="${project.id}">Archive</button></div></article>`; }
  document.addEventListener("DOMContentLoaded", async () => {
    const main = ui.shell("projects", "Projects", "Create, search, and organize extraction workspaces for every target domain.");
    if (!main || !ui.requireAuth()) return;
    const session = ui.currentSession();
    main.innerHTML = `<section class="card"><div class="card-body"><div class="table-controls"><div class="inline-field-row" style="flex:1"><input id="projectSearch" style="min-width:280px" placeholder="Search projects"><select id="projectFilter"><option value="all">All statuses</option><option value="active">Active</option><option value="archived">Archived</option></select></div><button class="button" id="newProjectBtn">New project</button></div></div></section><section id="projectGrid" class="project-grid"></section>`;
    const grid = main.querySelector("#projectGrid");
    let projects = await api.getProjects(session.id);
    function paint() {
      const search = main.querySelector("#projectSearch").value.trim().toLowerCase();
      const filter = main.querySelector("#projectFilter").value;
      const filtered = projects.filter((project) => (filter === "all" || project.status === filter) && (!search || project.name.toLowerCase().includes(search) || (project.description || "").toLowerCase().includes(search)));
      ui.renderList(grid, filtered, projectCard, "No projects matched the current filters.");
      grid.querySelectorAll("[data-open]").forEach((link) => link.addEventListener("click", () => ui.setActiveProject(projects.find((item) => item.id === link.dataset.open))));
      grid.querySelectorAll("[data-rename]").forEach((button) => button.addEventListener("click", () => ui.modal({ title: "Rename project", body: `<div class='field'><label>New name</label><input id='renameField' value='${ui.escapeHtml(projects.find((item) => item.id === button.dataset.rename).name)}'></div>`, confirmText: "Save", onConfirm: async (backdrop) => { const value = backdrop.querySelector("#renameField").value.trim(); if (value) { const project = projects.find((item) => item.id === button.dataset.rename); project.name = value; project.updated_at = new Date().toISOString(); ui.toast("Project renamed", "success"); paint(); } } } )));
      grid.querySelectorAll("[data-delete]").forEach((button) => button.addEventListener("click", () => ui.modal({ title: "Archive project", body: "This keeps the data but removes it from active work.", confirmText: "Archive", tone: "danger", onConfirm: async () => { const project = projects.find((item) => item.id === button.dataset.delete); project.status = "archived"; project.updated_at = new Date().toISOString(); ui.toast("Project archived", "success"); paint(); } } )));
    }
    paint();
    main.querySelector("#projectSearch").addEventListener("input", paint);
    main.querySelector("#projectFilter").addEventListener("change", paint);
    main.querySelector("#newProjectBtn").addEventListener("click", () => ui.modal({ title: "Create project", body: `<div class='form-grid'><div class='field'><label>Project name</label><input id='newProjectName' placeholder='Review Harvest'></div><div class='field'><label>Target domain</label><input id='newProjectDomain' placeholder='trustpilot.com'></div><div class='field' style='grid-column:1 / -1'><label>Description</label><textarea id='newProjectDescription' placeholder='Describe what the extraction should capture'></textarea></div></div>`, confirmText: "Create", onConfirm: async (backdrop) => { const payload = { user_id: session.id, name: backdrop.querySelector("#newProjectName").value.trim(), description: backdrop.querySelector("#newProjectDescription").value.trim(), domain: backdrop.querySelector("#newProjectDomain").value.trim() }; if (!payload.name) { ui.toast("Project name is required", "error"); return; } const project = await api.createProject(payload); project.domain = payload.domain || "pending"; projects.unshift(project); ui.setActiveProject(project); ui.toast("Project created", "success"); paint(); } }));
  });
})();
