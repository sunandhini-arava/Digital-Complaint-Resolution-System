/* ============================================================
   CMS - Login Page Script
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  // Redirect if already logged in
  if (Auth.isLoggedIn()) {
    redirectByRole(Auth.getUser()?.user_type);
    return;
  }

  const form       = document.getElementById('loginForm');
  const errorMsg   = document.getElementById('errorMessage');
  const successMsg = document.getElementById('successMessage');
  const submitBtn  = form.querySelector('button[type="submit"]');

  function showError(msg) {
    errorMsg.textContent = msg;
    errorMsg.style.display = 'block';
    successMsg.style.display = 'none';
  }
  function showSuccess(msg) {
    successMsg.textContent = msg;
    successMsg.style.display = 'block';
    errorMsg.style.display = 'none';
  }
  function clearMessages() {
    errorMsg.style.display = 'none';
    successMsg.style.display = 'none';
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearMessages();

    const user_id  = document.getElementById('user_id').value.trim();
    const password = document.getElementById('password').value;

    if (!user_id || !password) {
      showError('Please enter your User ID and password.');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Signing in…';

    try {
      const data = await api.post('/auth/login', { user_id, password });
      Auth.setToken(data.token);
      Auth.setUser(data.user);
      showSuccess('Login successful! Redirecting…');
      setTimeout(() => redirectByRole(data.user.user_type), 600);
    } catch (err) {
      showError(err.message || 'Login failed. Please try again.');
      submitBtn.disabled = false;
      submitBtn.textContent = 'Sign In';
    }
  });

  function redirectByRole(userType) {
    const routes = {
      student:        '/student-dashboard.html',
      faculty:        '/student-dashboard.html',
      administration: '/admin-dashboard.html',
      admin:          '/super-admin-dashboard.html',
    };
    window.location.href = routes[userType] || '/student-dashboard.html';
  }
});
