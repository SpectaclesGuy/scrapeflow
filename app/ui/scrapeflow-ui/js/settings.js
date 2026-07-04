(function () {
  const ui = window.ScrapeFlowUI;
  document.addEventListener('DOMContentLoaded', () => {
    const main = ui.shell('settings', 'Settings', 'Only the controls that matter day to day.');
    if (!main || !ui.requireAuth()) return;
    const session = ui.currentSession();
    main.innerHTML = `
      <section class='settings-grid compact-settings-grid'>
        <div class='card'>
          <div class='card-header'><p class='eyebrow'>Profile</p><h2 style='margin:0;font-size:20px'>Identity</h2></div>
          <div class='card-body'>
            <form id='profileForm' class='section-grid'>
              <div class='field'><label>Name</label><input name='name' value='${ui.escapeHtml(session.name)}'></div>
              <div class='field'><label>Email</label><input name='email' value='${ui.escapeHtml(session.email)}'></div>
              <div class='form-actions'><button class='button' type='submit'>Save locally</button></div>
            </form>
          </div>
        </div>
        <div class='card'>
          <div class='card-header'><p class='eyebrow'>Environment</p><h2 style='margin:0;font-size:20px'>App mode</h2></div>
          <div class='card-body section-grid'>
            <div class='list-item'>
              <div><div style='font-weight:700'>Mock mode</div><div class='inline-meta'><span>Use fallback data when APIs are incomplete.</span></div></div>
              <button class='button-secondary' id='toggleMock'>${window.ScrapeFlowAPI.useMock() ? 'Disable' : 'Enable'}</button>
            </div>
            <div class='list-item'>
              <div><div style='font-weight:700'>API base URL</div><div class='inline-meta'><span>${window.ScrapeFlowConfig.API_BASE_URL}</span></div></div>
              <button class='button-ghost' id='changeApi'>Change</button>
            </div>
          </div>
        </div>
      </section>`;
    main.querySelector('#profileForm').addEventListener('submit', (event) => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      ui.setSession({ ...session, name: form.get('name'), email: form.get('email') });
      ui.toast('Profile updated locally', 'success');
    });
    main.querySelector('#toggleMock').addEventListener('click', () => {
      const next = !window.ScrapeFlowAPI.useMock();
      window.ScrapeFlowAPI.setMockMode(next);
      ui.toast(`Mock mode ${next ? 'enabled' : 'disabled'}`, 'success');
      setTimeout(() => window.location.reload(), 250);
    });
    main.querySelector('#changeApi').addEventListener('click', () => ui.modal({ title: 'Change API base URL', body: `<div class='field'><label>Base URL</label><input id='apiBaseField' value='${ui.escapeHtml(window.ScrapeFlowConfig.API_BASE_URL)}'></div>`, confirmText: 'Save', onConfirm: async (backdrop) => { localStorage.setItem('sf_api_base_url', backdrop.querySelector('#apiBaseField').value.trim()); ui.toast('API base URL updated', 'success'); setTimeout(() => window.location.reload(), 250); } }));
  });
})();
