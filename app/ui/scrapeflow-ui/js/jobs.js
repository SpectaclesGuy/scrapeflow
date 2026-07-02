(function () {
  const ui = window.ScrapeFlowUI;
  const api = window.ScrapeFlowAPI;
  document.addEventListener("DOMContentLoaded", async () => {
    const main = ui.shell("jobs", "Jobs", "Track queued, running, completed, and failed extraction workloads with project-aware status filters.");
    if (!main || !ui.requireAuth()) return;
    const projectId = new URLSearchParams(window.location.search).get("project") || ui.getActiveProject()?.id;
    if (!projectId) { main.innerHTML = `<div class='empty-state'>Open a project first.</div>`; return; }
    let jobs = await api.getJobs(projectId);
    main.innerHTML = `<section class='card table-card'><div class='card-body'><div class='table-controls'><div class='inline-field-row'><select id='jobFilter'><option value='all'>All statuses</option><option value='created'>Created</option><option value='queued'>Queued</option><option value='running'>Running</option><option value='completed'>Completed</option><option value='failed'>Failed</option></select></div><a class='button' href='/plan.html?project=${projectId}'>Run new extraction</a></div><div class='table-wrap'><table class='data-table'><thead><tr><th>Job ID</th><th>Status</th><th>Started</th><th>Updated</th><th>Records</th><th>Pages</th><th>Actions</th></tr></thead><tbody id='jobsBody'></tbody></table></div></div></section>`;
    const body = main.querySelector("#jobsBody");
    function paint() {
      const filter = main.querySelector("#jobFilter").value;
      const filtered = jobs.filter((job) => filter === "all" || job.status === filter);
      body.innerHTML = filtered.length ? filtered.map((job) => `<tr><td>${job.id}</td><td><span class='${ui.statusClass(job.status)}'>${job.status}</span></td><td>${ui.formatDate(job.created_at)}</td><td>${ui.formatDate(job.updated_at)}</td><td>${job.config?.records ?? "-"}</td><td>${job.config?.pages ?? "-"}</td><td><div class='table-actions'><a class='button-secondary' href='/job.html?project=${projectId}&job=${job.id}'>Open</a><button class='button-ghost' data-advance='${job.id}'>Advance</button></div></td></tr>`).join("") : `<tr><td colspan='7'><div class='empty-state'>No jobs found.</div></td></tr>`;
      body.querySelectorAll("[data-advance]").forEach((button) => button.addEventListener("click", async () => { const cycle = { created: "queued", queued: "running", running: "completed", failed: "queued", completed: "completed" }; const current = jobs.find((job) => job.id === button.dataset.advance); const next = cycle[current.status] || "running"; const updated = await api.updateJob(current.id, { status: next, config: { ...(current.config || {}), records: next === "completed" ? 214 : current.config?.records || 0, pages: next === "completed" ? 14 : current.config?.pages || 0 } }); jobs = jobs.map((job) => job.id === updated.id ? updated : job); ui.toast(`Job moved to ${next}`, "success"); paint(); }));
    }
    paint();
    main.querySelector("#jobFilter").addEventListener("change", paint);
  });
})();
