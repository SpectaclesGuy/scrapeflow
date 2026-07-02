(function () {
  const ui = window.ScrapeFlowUI;
  const api = window.ScrapeFlowAPI;
  document.addEventListener("DOMContentLoaded", async () => {
    const main = ui.shell("results", "Results", "Preview extracted records with filters, confidence signals, and evidence-ready review actions.");
    if (!main || !ui.requireAuth()) return;
    const results = await api.getResults();
    main.innerHTML = `<section class='card table-card'><div class='card-body'><div class='table-controls'><div class='inline-field-row'><input id='resultSearch' placeholder='Search results'><select id='resultFilter'><option value='all'>All statuses</option><option value='valid'>Valid</option><option value='warning'>Warning</option></select></div><div class='quick-actions'><button class='button-secondary'>Download CSV</button><button class='button-secondary'>Download Excel</button><button class='button'>Download JSON</button></div></div><div class='table-wrap'><table class='data-table'><thead><tr><th>Title</th><th>Project</th><th>Source</th><th>Rating</th><th>Verified</th><th>Validation</th><th>Evidence</th></tr></thead><tbody id='resultsBody'></tbody></table></div><div class='pagination-row'><span class='page-subtitle'>Interactive preview backed by mock or API fallback data.</span><span class='kbd'>1 / 1</span></div></div></section>`;
    const body = main.querySelector("#resultsBody");
    function paint() {
      const search = main.querySelector("#resultSearch").value.toLowerCase();
      const filter = main.querySelector("#resultFilter").value;
      const filtered = results.filter((row) => (filter === "all" || row.status === filter) && (!search || row.title.toLowerCase().includes(search) || row.source.toLowerCase().includes(search)));
      body.innerHTML = filtered.length ? filtered.map((row) => `<tr><td>${row.title}</td><td>${row.project}</td><td>${row.source}</td><td>${row.rating}</td><td>${row.verified ? "Yes" : "No"}</td><td><span class='${ui.statusClass(row.status === "warning" ? "failed" : "completed")}' >${row.status}</span></td><td><code>${row.evidence}</code></td></tr>`).join("") : `<tr><td colspan='7'><div class='empty-state'>No result rows matched the filters.</div></td></tr>`;
    }
    paint();
    main.querySelector("#resultSearch").addEventListener("input", paint);
    main.querySelector("#resultFilter").addEventListener("change", paint);
  });
})();
