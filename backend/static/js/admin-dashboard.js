/* ============================================================
   CMS - Admin (Administration) Dashboard Script
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  const user = requireLogin();
  if (!user) return;
  if (!['administration', 'admin'].includes(user.user_type)) {
    window.location.href = '/login.html'; return;
  }

  // ── Header ───────────────────────────────────────────────
  document.getElementById('userName').textContent = user.full_name;
  document.getElementById('profileUserId').textContent = user.user_id;
  document.getElementById('profileName').textContent   = user.full_name;
  document.getElementById('profileEmail').textContent  = user.email || '—';
  document.getElementById('profileType').textContent   = user.user_type;

  // ── Sidebar nav ──────────────────────────────────────────
  const pageIdMap = {
    'dashboard':       'dashboardPage',
    'all-complaints':  'allComplaintsPage',
    'pending':         'pendingPage',
    'in-progress':     'inProgressPage',
    'resolved':        'resolvedPage',
    'profile':         'profilePage',
  };
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const page = link.dataset.page;
      document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
      link.classList.add('active');
      document.querySelectorAll('.page-content').forEach(p => p.classList.remove('active'));
      document.getElementById(pageIdMap[page])?.classList.add('active');
      const loaders = {
        'dashboard':      loadDashboard,
        'all-complaints': () => loadComplaints('allComplaintsList', {}),
        'pending':        () => loadComplaints('pendingComplaintsList', { status: 'pending' }),
        'in-progress':    () => loadComplaints('inProgressComplaintsList', { status: 'in-progress' }),
        'resolved':       () => loadComplaints('resolvedComplaintsList', { status: 'resolved' }),
      };
      loaders[page]?.();
    });
  });

  document.getElementById('logoutBtn').addEventListener('click', () => {
    Auth.clear(); window.location.href = '/login.html';
  });

  // ── Dashboard ────────────────────────────────────────────
  async function loadDashboard() {
    try {
      const { stats } = await api.get('/stats/dashboard');
      document.getElementById('totalComplaints').textContent   = stats.total_complaints || 0;
      const pending  = stats.by_status?.find(s => s.status === 'pending')?.count     || 0;
      const progress = stats.by_status?.find(s => s.status === 'in-progress')?.count || 0;
      const resolved = stats.by_status?.find(s => s.status === 'resolved')?.count    || 0;
      document.getElementById('pendingComplaints').textContent    = pending;
      document.getElementById('inProgressComplaints').textContent = progress;
      document.getElementById('resolvedComplaints').textContent   = resolved;

      renderRecentList(stats.recent_complaints || []);

      const colorMap = {
        academic:'#4f46e5', infrastructure:'#10b981', administrative:'#f59e0b',
        technical:'#3b82f6', hostel:'#8b5cf6', transport:'#ef4444', other:'#94a3b8'
      };
      renderBarChart('categoryChart', stats.by_category || [], 'category', 'count',
        (cat) => colorMap[cat] || '#94a3b8');
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  function renderRecentList(list) {
    const container = document.getElementById('recentComplaintsList');
    if (!list.length) {
      container.innerHTML = `<div class="empty-state"><div class="empty-icon">📭</div><p>No complaints yet</p></div>`;
      return;
    }
    container.innerHTML = list.map(c => `
      <div class="complaint-card" data-id="${esc(c.complaint_id)}" style="cursor:pointer">
        <div class="complaint-card-header">
          <div>
            <div class="complaint-title">${esc(c.title)}</div>
            <div class="complaint-meta">
              <span class="complaint-id">${esc(c.complaint_id)}</span>
              <span>${timeAgo(c.created_at)}</span>
            </div>
          </div>
          <div style="display:flex;gap:6px">${statusBadge(c.status)}${priorityBadge(c.priority||'medium')}</div>
        </div>
      </div>`).join('');
    container.querySelectorAll('.complaint-card').forEach(card =>
      card.addEventListener('click', () => openComplaintModal(card.dataset.id)));
  }

  // ── All Complaints ───────────────────────────────────────
  let currentFilters = {};
  let currentPage = 1;

  async function loadComplaints(containerId, filters = {}, page = 1) {
    currentFilters = filters;
    currentPage = page;
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '<div class="empty-state"><div class="spinner" style="margin:0 auto"></div></div>';
    try {
      const params = { ...filters, page, per_page: 15 };
      const { complaints, pagination } = await api.get('/complaints', params);
      if (!complaints.length) {
        container.innerHTML = `<div class="empty-state"><div class="empty-icon">📭</div><p>No complaints found</p></div>`;
        return;
      }
      container.innerHTML = complaints.map(c => `
        <div class="complaint-card" data-id="${esc(c.complaint_id)}">
          <div class="complaint-card-header">
            <div>
              <div class="complaint-title">${esc(c.title)}</div>
              <div class="complaint-meta">
                <span class="complaint-id">${esc(c.complaint_id)}</span>
                <span>${esc(c.category)}</span>
                <span class="badge badge-${esc(c.user_type)}">${esc(c.user_name)}</span>
                <span>${timeAgo(c.created_at)}</span>
              </div>
            </div>
            <div style="display:flex;gap:6px;flex-shrink:0">${statusBadge(c.status)}${priorityBadge(c.priority||'medium')}</div>
          </div>
          <div class="complaint-description">${esc(c.description)}</div>
        </div>`).join('');

      container.querySelectorAll('.complaint-card').forEach(card =>
        card.addEventListener('click', () => openComplaintModal(card.dataset.id)));

      // Pagination
      if (pagination && pagination.pages > 1) {
        const pager = document.createElement('div');
        pager.className = 'pagination';
        pager.innerHTML = `
          <button class="page-btn" ${page<=1?'disabled':''} data-p="${page-1}">← Prev</button>
          <span style="font-size:.875rem;color:var(--text-muted)">Page ${page} / ${pagination.pages} (${pagination.total} total)</span>
          <button class="page-btn" ${page>=pagination.pages?'disabled':''} data-p="${page+1}">Next →</button>`;
        pager.querySelectorAll('[data-p]').forEach(btn =>
          btn.addEventListener('click', () => loadComplaints(containerId, filters, +btn.dataset.p)));
        container.appendChild(pager);
      }
    } catch (err) {
      container.innerHTML = `<div class="empty-state"><p style="color:var(--danger)">${err.message}</p></div>`;
    }
  }

  // Search & filter for all-complaints page
  let searchDebounce = null;
  document.getElementById('searchInput')?.addEventListener('input', (e) => {
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => {
      loadComplaints('allComplaintsList', {
        ...currentFilters,
        search: e.target.value.trim(),
        category: document.getElementById('categoryFilter')?.value || ''
      });
    }, 400);
  });

  document.getElementById('categoryFilter')?.addEventListener('change', (e) => {
    loadComplaints('allComplaintsList', {
      ...currentFilters,
      category: e.target.value,
      search: document.getElementById('searchInput')?.value.trim() || ''
    });
  });

  // ── Complaint Detail Modal ───────────────────────────────
  let activeComplaintId = null;

  async function openComplaintModal(complaintId) {
    activeComplaintId = complaintId;
    try {
      const { complaint } = await api.get(`/complaints/${complaintId}`);
      document.getElementById('complaintDetails').innerHTML = `
        <div class="complaint-details-grid">
          <div class="detail-item">
            <label>Complaint ID</label><code>${esc(complaint.complaint_id)}</code>
          </div>
          <div class="detail-item">
            <label>Submitted By</label>
            <span>${esc(complaint.user_name)} <span class="badge badge-${esc(complaint.user_type)}">${esc(complaint.user_type)}</span></span>
          </div>
          <div class="detail-item">
            <label>Status</label>${statusBadge(complaint.status)}
          </div>
          <div class="detail-item">
            <label>Priority</label>${priorityBadge(complaint.priority||'medium')}
          </div>
          <div class="detail-item">
            <label>Category</label><span>${esc(complaint.category)}</span>
          </div>
          <div class="detail-item">
            <label>Submitted</label><span>${formatDate(complaint.created_at)}</span>
          </div>
          <div class="detail-item detail-full">
            <label>Title</label><strong>${esc(complaint.title)}</strong>
          </div>
          <div class="detail-item detail-full">
            <label>Description</label>
            <p style="white-space:pre-wrap;background:var(--bg);padding:10px;border-radius:8px">${esc(complaint.description)}</p>
          </div>
          ${complaint.admin_remarks ? `<div class="detail-item detail-full"><label>Remarks</label><p>${esc(complaint.admin_remarks)}</p></div>` : ''}
          ${complaint.attachment_path ? `<div class="detail-item detail-full"><label>Attachment</label><a href="/api/uploads/${esc(complaint.attachment_path)}" target="_blank" class="btn btn-sm btn-secondary">📎 View Attachment</a></div>` : ''}
        </div>
        ${complaint.updates?.length ? `
        <div class="updates-timeline">
          <h4 style="margin-bottom:8px">Activity Log</h4>
          ${complaint.updates.map(u => `
            <div class="update-item">
              <div class="update-dot"></div>
              <div>
                <div><strong>${esc(u.updated_by_name)}</strong>
                  ${u.update_type === 'status_change'
                    ? ` changed status: ${statusBadge(u.old_status)} → ${statusBadge(u.new_status)}`
                    : ` commented`}
                </div>
                ${u.message ? `<div style="font-size:.85rem;color:var(--text-secondary)">${esc(u.message)}</div>` : ''}
                <div class="update-meta">${timeAgo(u.created_at)}</div>
              </div>
            </div>`).join('')}
        </div>` : ''}
      `;

      // Pre-fill update form
      document.getElementById('updateStatus').value   = complaint.status;
      document.getElementById('updatePriority').value = complaint.priority || 'medium';
      document.getElementById('adminRemarks').value   = '';
      openModal('complaintModal');
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  // Close modal
  document.querySelectorAll('.close').forEach(btn => {
    btn.addEventListener('click', () => closeModal('complaintModal'));
  });
  document.getElementById('complaintModal')?.addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeModal('complaintModal');
  });

  // Submit complaint update
  document.getElementById('updateComplaintForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    const updateMsg = document.getElementById('updateMessage');
    try {
      await api.put(`/complaints/${activeComplaintId}/update`, {
        status:        document.getElementById('updateStatus').value,
        priority:      document.getElementById('updatePriority').value,
        admin_remarks: document.getElementById('adminRemarks').value.trim(),
      });
      updateMsg.textContent = 'Complaint updated successfully!';
      updateMsg.className = 'form-message success';
      updateMsg.style.display = 'block';
      showToast('Complaint updated!', 'success');
      closeModal('complaintModal');
      loadDashboard();
      loadComplaints('allComplaintsList', {});
    } catch (err) {
      updateMsg.textContent = err.message;
      updateMsg.className = 'form-message error';
      updateMsg.style.display = 'block';
    } finally {
      btn.disabled = false;
    }
  });

  // ── Change password ──────────────────────────────────────
  document.getElementById('changePasswordForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const msg = document.getElementById('passwordMessage');
    const new_password = document.getElementById('newPassword').value;
    if (new_password !== document.getElementById('confirmNewPassword').value) {
      msg.textContent = 'Passwords do not match.';
      msg.className = 'form-message error'; msg.style.display = 'block'; return;
    }
    try {
      const data = await api.post('/auth/reset-password', {
        old_password: document.getElementById('oldPassword').value,
        new_password
      });
      msg.textContent = data.message;
      msg.className = 'form-message success'; msg.style.display = 'block';
      e.target.reset();
    } catch (err) {
      msg.textContent = err.message;
      msg.className = 'form-message error'; msg.style.display = 'block';
    }
  });

  // ── Initial load ─────────────────────────────────────────
  loadDashboard();
});
