(function () {
  const ui = window.ScrapeFlowUI;
  const api = window.ScrapeFlowAPI;
  document.addEventListener("DOMContentLoaded", async () => {
    const main = ui.shell("jobs", "Job detail", "Inspect progress, watch status transitions, and keep the extraction run inside an observable feedback loop.");
    if (!main || !ui.requireAuth()) return;
    const params = new URLSearchParams(window.location.search);
    const projectId = params.get("project") || ui.getActiveProject()?.id;
    const jobId = params.get("job");
    if (!projectId || !jobId) { main.innerHTML = `<div class='empty-state'>Open a job from the Jobs page.</div>`; return; }
    const job = (await api.getJobs(projectId)).find((item) => item.id === jobId);
    const progress = job.status === "completed" ? 100 : job.status === "running" ? 68 : job.status === "queued" ? 20 : job.status === "failed" ? 42 : 8;
    main.innerHTML = `<section class='panel-grid'><div class='card'><div class='card-header'><p class='eyebrow'>Execution progress</p><h2 style='margin:0;font-size:24px'>${job.id}</h2></div><div class='card-body section-grid'><div class='list-item'><div><div style='font-weight:700'>Status</div><div class='inline-meta'><span class='${ui.statusClass(job.status)}'>${job.status}</span></div></div><span>${progress}%</span></div><div style='height:12px;border-radius:999px;background:#e5e7eb;overflow:hidden'><div style='width:${progress}%;height:100%;background:linear-gradient(90deg,#2563eb,#60a5fa)'></div></div><div class='list'><div class='list-item'><div><div style='font-weight:700'>Current URL</div><div class='inline-meta'><span>${job.config?.target_url || "Waiting for browser navigation"}</span></div></div></div><div class='list-item'><div><div style='font-weight:700'>Records extracted</div><div class='inline-meta'><span>${job.config?.records || 0}</span></div></div></div><div class='list-item'><div><div style='font-weight:700'>Errors</div><div class='inline-meta'><span>${job.error_message || "No errors recorded"}</span></div></div></div></div><div class='quick-actions'><button class='button-secondary' id='retryJob'>Retry</button><button class='button-ghost' id='cancelJob'>Cancel</button><a class='button' href='/results.html?project=${projectId}'>Preview results</a></div></div></div><div class='card'><div class='card-header'><p class='eyebrow'>Job configuration</p><h2 style='margin:0;font-size:24px'>Runtime payload</h2></div><div class='card-body'><pre style='margin:0'>${ui.escapeHtml(JSON.stringify(job, null, 2))}</pre></div></div></section>`;
    main.querySelector("#retryJob").addEventListener("click", async () => { await api.updateJob(job.id, { status: "queued" }); ui.toast("Job queued for retry", "success"); window.location.reload(); });
    main.querySelector("#cancelJob").addEventListener("click", async () => { await api.updateJob(job.id, { status: "failed", error_message: "Cancelled from dashboard." }); ui.toast("Job cancelled", "success"); window.location.reload(); });
  });
})();
