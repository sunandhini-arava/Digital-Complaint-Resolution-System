/* ============================================================
   CMS - Shared API & Utility Helpers
   ============================================================ */

const API_BASE = '/api';

// ─── Storage helpers ──────────────────────────────────────
const Auth = {
  setToken: (token) => localStorage.setItem('cms_token', token),
  getToken: ()      => localStorage.getItem('cms_token'),
  setUser:  (user)  => localStorage.setItem('cms_user', JSON.stringify(user)),
  getUser:  ()      => { try { return JSON.parse(localStorage.getItem('cms_user')); } catch { return null; } },
  clear:    ()      => { localStorage.removeItem('cms_token'); localStorage.removeItem('cms_user'); },
  isLoggedIn: ()    => !!localStorage.getItem('cms_token'),
};

// ─── API Request ──────────────────────────────────────────
async function apiRequest(method, path, data = null, isFormData = false) {
  const token = Auth.getToken();
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const options = { method, headers };

  if (data && !isFormData) {
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(data);
  } else if (data && isFormData) {
    options.body = data; // FormData, no Content-Type header
  }

  const res = await fetch(`${API_BASE}${path}`, options);
  const json = await res.json().catch(() => ({ message: 'Empty response' }));

  if (res.status === 401) {
    Auth.clear();
    window.location.href = '/login.html';
    return;
  }

  if (!res.ok) {
    throw new Error(json.message || `HTTP ${res.status}`);
  }

  return json;
}

const api = {
  get:    (path, params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest('GET', path + (qs ? '?' + qs : ''));
  },
  post:   (path, data)     => apiRequest('POST',   path, data),
  put:    (path, data)     => apiRequest('PUT',    path, data),
  delete: (path)           => apiRequest('DELETE', path),
  postForm: (path, fd)     => apiRequest('POST',   path, fd, true),
};

// ─── Toast Notifications ──────────────────────────────────
function ensureToastContainer() {
  if (!document.getElementById('toastContainer')) {
    const el = document.createElement('div');
    el.id = 'toastContainer';
    el.className = 'toast-container';
    document.body.appendChild(el);
  }
  return document.getElementById('toastContainer');
}

function showToast(message, type = 'default', duration = 3500) {
  const container = ensureToastContainer();
  const icons = { success: '✅', error: '❌', warning: '⚠️', default: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || icons.default}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'none';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all .25s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ─── Modal helpers ────────────────────────────────────────
function openModal(id) {
  const m = document.getElementById(id);
  if (m) { m.classList.add('open'); m.style.display = 'flex'; }
}
function closeModal(id) {
  const m = document.getElementById(id);
  if (m) { m.classList.remove('open'); m.style.display = 'none'; }
}

// ─── Badge helpers ────────────────────────────────────────
function statusBadge(status) {
  return `<span class="badge badge-${status}">${status}</span>`;
}
function priorityBadge(priority) {
  return `<span class="badge badge-${priority}">${priority}</span>`;
}

// ─── Date formatting ──────────────────────────────────────
function formatDate(dateStr) {
  if (!dateStr) return '—';
  try {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  } catch { return dateStr; }
}

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  return formatDate(dateStr);
}

// ─── Guard: require login ─────────────────────────────────
function requireLogin(expectedType = null) {
  if (!Auth.isLoggedIn()) {
    window.location.href = '/login.html';
    return null;
  }
  const user = Auth.getUser();
  if (expectedType && user?.user_type !== expectedType) {
    const routes = {
      student: '/student-dashboard.html',
      faculty: '/student-dashboard.html',
      administration: '/admin-dashboard.html',
      admin: '/super-admin-dashboard.html',
    };
    window.location.href = routes[user?.user_type] || '/login.html';
    return null;
  }
  return user;
}

// ─── Simple bar chart renderer ────────────────────────────
function renderBarChart(containerId, items, labelKey, valueKey, colorFn) {
  const container = document.getElementById(containerId);
  if (!container || !items || !items.length) return;
  const max = Math.max(...items.map(i => i[valueKey] || 0)) || 1;
  container.innerHTML = items.map(item => `
    <div class="chart-bar-wrap">
      <span class="chart-value">${item[valueKey] || 0}</span>
      <div class="chart-bar" style="height:${Math.round((item[valueKey] / max) * 140)}px;background:${colorFn ? colorFn(item[labelKey]) : 'var(--primary)'}"></div>
      <span class="chart-label">${item[labelKey] || '—'}</span>
    </div>
  `).join('');
}

// ─── Escape HTML ──────────────────────────────────────────
function esc(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
