(function () {
  const ui = window.ScrapeFlowUI;
  const api = window.ScrapeFlowAPI;
  document.addEventListener("DOMContentLoaded", async () => {
    const main = ui.shell("exports", "Exports", "Track generated deliveries and hand structured datasets to downstream consumers in the right format.");
    if (!main || !ui.requireAuth()) return;
    const exportsList = await api.getExports();
    main.innerHTML = `<section class='export-grid' id='exportsGrid'></section>`;
    const grid = main.querySelector("#exportsGrid");
    ui.renderList(grid, exportsList, (item) => `<article class='card export-card'><div class='export-card-header'><div><div class='project-card-title'>${item.name}</div><div class='inline-meta'><span>${item.format}</span><span>${ui.formatDate(item.created_at)}</span></div></div><span class='kbd'>${item.size}</span></div><p class='project-card-copy'>Structured delivery artifact ready for download or regeneration.</p><div class='quick-actions'><button class='button'>Download</button><button class='button-secondary'>Regenerate</button></div></article>`, "No exports generated yet.");
  });
})();
