(function () {
  const ui = window.ScrapeFlowUI;
  const api = window.ScrapeFlowAPI;

  async function login(formData) {
    const email = formData.get('email').toString().trim();
    const password = formData.get('password').toString();
    if (!email || !password) throw new Error('Email and password are required.');
    const user = await api.login({ email, password });
    ui.setSession(user);
    return user;
  }

  async function signup(formData) {
    const name = formData.get('name').toString().trim();
    const email = formData.get('email').toString().trim();
    const password = formData.get('password').toString();
    const confirm = formData.get('confirmPassword').toString();
    if (!name || !email || !password) throw new Error('All fields are required.');
    if (password.length < 8) throw new Error('Password must be at least 8 characters.');
    if (password !== confirm) throw new Error('Passwords do not match.');
    const user = await api.signup({ name, email, password });
    ui.setSession(user);
    return user;
  }

  function beginGoogleLogin() {
    api.beginGoogleLogin();
  }

  window.ScrapeFlowAuth = { login, signup, beginGoogleLogin };
})();
