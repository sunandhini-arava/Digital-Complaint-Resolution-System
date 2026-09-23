/* ============================================================
   CMS - Account Activation Script
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  const form       = document.getElementById('activateForm');
  const errorMsg   = document.getElementById('errorMessage');
  const successMsg = document.getElementById('successMessage');
  const submitBtn  = form.querySelector('button[type="submit"]');

  function showError(msg)   { errorMsg.textContent = msg; errorMsg.style.display = 'block'; successMsg.style.display = 'none'; }
  function showSuccess(msg) { successMsg.textContent = msg; successMsg.style.display = 'block'; errorMsg.style.display = 'none'; }

  // Step 1: verify user ID exists
  const userIdInput = document.getElementById('user_id');
  const step2       = document.getElementById('step2');
  const userIdStatus = document.getElementById('userIdStatus');

  userIdInput.addEventListener('blur', async () => {
    const user_id = userIdInput.value.trim();
    if (!user_id) return;
    try {
      const data = await api.post('/auth/check-user', { user_id });
      if (data.is_activated) {
        userIdStatus.textContent = '⚠️ This account is already activated. Please login.';
        userIdStatus.className = 'form-hint error-text';
        step2.style.display = 'none';
      } else {
        userIdStatus.textContent = '✓ User found. Please complete activation below.';
        userIdStatus.className = 'form-hint success-text';
        step2.style.display = 'block';
      }
    } catch (err) {
      userIdStatus.textContent = err.message || 'User ID not found.';
      userIdStatus.className = 'form-hint error-text';
      step2.style.display = 'none';
    }
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorMsg.style.display = 'none';
    successMsg.style.display = 'none';

    const user_id       = document.getElementById('user_id').value.trim();
    const birthdate     = document.getElementById('birthdate').value;
    const new_password  = document.getElementById('new_password').value;
    const confirm_pass  = document.getElementById('confirm_password').value;

    if (!user_id || !birthdate || !new_password) {
      showError('All fields are required.'); return;
    }
    if (new_password.length < 8) {
      showError('Password must be at least 8 characters.'); return;
    }
    if (new_password !== confirm_pass) {
      showError('Passwords do not match.'); return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Activating…';

    try {
      const data = await api.post('/auth/activate', { user_id, birthdate, new_password });
      showSuccess(data.message + ' Redirecting to login…');
      setTimeout(() => window.location.href = '/login.html', 2000);
    } catch (err) {
      showError(err.message || 'Activation failed.');
      submitBtn.disabled = false;
      submitBtn.textContent = 'Activate Account';
    }
  });
});
