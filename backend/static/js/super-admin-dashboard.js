/* ============================================================
   CMS - Super Admin Dashboard Script
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  const user = requireLogin();
  if (!user) return;
  if (user.user_type !== 'admin') {
    window.location.href = '/login.html'; return;
  }

  document.getElementById('userName').textContent    = user.full_name;
  document.getElementById('profileUserId').textContent = user.user_id;
  document.getElementById('profileName').textContent   = user.full_name;
  document.getElementById('profileEmail').textContent  = user.email || '—';
  document.getElementById('profileType').textContent   = 'Super Admin';

  const pageIdMap = {
    'dashboard':       'dashboardPage',
    'all-complaints':  'allComplaintsPage',
    'user-management': 'userManagementPage',
    'reports':         'reportsPage',
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
        'dashboard':       loadDashboard,
        'all-complaints':  loadAllComplaints,
        'user-management': loadUsers,
        'reports':         loadReports,
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
      document.getElementById('totalUsers').textContent        = stats.total_users       || 0;
      const pending  = stats.by_status?.find(s => s.status === 'pending')?.count     || 0;
      const progress = stats.by_status?.find(s => s.status === 'in-progress')?.count || 0;
      const resolved = stats.by_status?.find(s => s.status === 'resolved')?.count    || 0;
      const students = stats.user_stats?.find(u => u.user_type === 'student')?.count || 0;
      const faculty  = stats.user_stats?.find(u => u.user_type === 'faculty')?.count || 0;
      const admins   = stats.user_stats?.find(u => u.user_type === 'administration')?.count || 0;
      document.getElementById('pendingComplaints').textContent    = pending;
      document.getElementById('inProgressComplaints').textContent = progress;
      document.getElementById('resolvedComplaints').textContent   = resolved;
      document.getElementById('totalStudents').textContent  = students;
      document.getElementById('totalFaculty').textContent   = faculty;
      document.getElementById('totalAdmins').textContent    = admins;
      document.getElementById('resolutionRate').textContent  = (stats.resolution_rate || 0) + '%';
      document.getElementById('avgResolutionDays').textContent = (stats.avg_resolution_days || 0) + 'd';

      renderRecentList(stats.recent_complaints || []);

      const colorMap = {
        academic:'#4f46e5', infrastructure:'#10b981', administrative:'#f59e0b',
        technical:'#3b82f6', hostel:'#8b5cf6', transport:'#ef4444', other:'#94a3b8'
      };
      renderBarChart('categoryChartDash', stats.by_category || [], 'category', 'count',
        cat => colorMap[cat] || '#94a3b8');
      renderBarChart('statusChartDash', stats.by_status || [], 'status', 'count',
        s => ({ pending:'#f59e0b','in-progress':'#3b82f6',resolved:'#10b981',closed:'#94a3b8',rejected:'#ef4444' }[s] || '#94a3b8'));
    } catch (err) { showToast(err.message, 'error'); }
  }

  function renderRecentList(list) {
    const container = document.getElementById('recentComplaintsList');
    if (!container) return;
    if (!list.length) { container.innerHTML = `<div class="empty-state"><div class="empty-icon">📭</div><p>No complaints</p></div>`; return; }
    container.innerHTML = list.map(c => `
      <div class="complaint-card" data-id="${esc(c.complaint_id)}" style="cursor:pointer">
        <div class="complaint-card-header">
          <div>
            <div class="complaint-title">${esc(c.title)}</div>
            <div class="complaint-meta"><span class="complaint-id">${esc(c.complaint_id)}</span><span>${timeAgo(c.created_at)}</span></div>
          </div>
          <div style="display:flex;gap:6px">${statusBadge(c.status)}${priorityBadge(c.priority||'medium')}</div>
        </div>
      </div>`).join('');
    container.querySelectorAll('.complaint-card').forEach(card =>
      card.addEventListener('click', () => openComplaintModal(card.dataset.id)));
  }

  // ── All Complaints ───────────────────────────────────────
  async function loadAllComplaints(filters = {}, page = 1) {
    const container = document.getElementById('superComplaintsList');
    if (!container) return;
    container.innerHTML = '<div class="empty-state"><div class="spinner" style="margin:0 auto"></div></div>';
    try {
      const search    = document.getElementById('superSearchInput')?.value.trim() || '';
      const category  = document.getElementById('superCategoryFilter')?.value || '';
      const status    = document.getElementById('superStatusFilter')?.value || '';
      const priority  = document.getElementById('superPriorityFilter')?.value || '';
      const params = { search, category, status, priority, page, per_page: 15, ...filters };
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

      if (pagination.pages > 1) {
        const pager = document.createElement('div');
        pager.className = 'pagination';
        pager.innerHTML = `
          <button class="page-btn" ${page<=1?'disabled':''} data-p="${page-1}">← Prev</button>
          <span style="font-size:.875rem;color:var(--text-muted)">Page ${page}/${pagination.pages} (${pagination.total})</span>
          <button class="page-btn" ${page>=pagination.pages?'disabled':''} data-p="${page+1}">Next →</button>`;
        pager.querySelectorAll('[data-p]').forEach(btn =>
          btn.addEventListener('click', () => loadAllComplaints({}, +btn.dataset.p)));
        container.appendChild(pager);
      }
    } catch (err) {
      container.innerHTML = `<div class="empty-state"><p style="color:var(--danger)">${err.message}</p></div>`;
    }
  }

  ['superSearchInput', 'superCategoryFilter', 'superStatusFilter', 'superPriorityFilter'].forEach(id => {
    let d = null;
    document.getElementById(id)?.addEventListener('input', () => { clearTimeout(d); d = setTimeout(() => loadAllComplaints(), 400); });
    document.getElementById(id)?.addEventListener('change', () => loadAllComplaints());
  });

  // ── Complaint Modal ──────────────────────────────────────
  let activeComplaintId = null;

  async function openComplaintModal(complaintId) {
    activeComplaintId = complaintId;
    try {
      const { complaint } = await api.get(`/complaints/${complaintId}`);
      document.getElementById('modalComplaintDetails').innerHTML = `
        <div class="complaint-details-grid">
          <div class="detail-item"><label>ID</label><code>${esc(complaint.complaint_id)}</code></div>
          <div class="detail-item"><label>By</label><span>${esc(complaint.user_name)} <span class="badge badge-${esc(complaint.user_type)}">${esc(complaint.user_type)}</span></span></div>
          <div class="detail-item"><label>Status</label>${statusBadge(complaint.status)}</div>
          <div class="detail-item"><label>Priority</label>${priorityBadge(complaint.priority||'medium')}</div>
          <div class="detail-item"><label>Category</label><span>${esc(complaint.category)}</span></div>
          <div class="detail-item"><label>Submitted</label><span>${formatDate(complaint.created_at)}</span></div>
          <div class="detail-item detail-full"><label>Title</label><strong>${esc(complaint.title)}</strong></div>
          <div class="detail-item detail-full"><label>Description</label>
            <p style="white-space:pre-wrap;background:var(--bg);padding:10px;border-radius:8px">${esc(complaint.description)}</p>
          </div>
          ${complaint.admin_remarks ? `<div class="detail-item detail-full"><label>Remarks</label><p>${esc(complaint.admin_remarks)}</p></div>` : ''}
          ${complaint.attachment_path ? `<div class="detail-item detail-full"><label>Attachment</label><a href="/api/uploads/${esc(complaint.attachment_path)}" target="_blank" class="btn btn-sm btn-secondary">📎 View</a></div>` : ''}
        </div>
        ${complaint.updates?.length ? `
        <div class="updates-timeline" style="margin-top:16px">
          <h4 style="margin-bottom:8px">Activity</h4>
          ${complaint.updates.map(u => `
            <div class="update-item">
              <div class="update-dot"></div>
              <div>
                <strong>${esc(u.updated_by_name)}</strong>
                ${u.update_type === 'status_change' ? ` changed status: ${statusBadge(u.old_status)} → ${statusBadge(u.new_status)}` : ` commented`}
                ${u.message ? `<div style="font-size:.85rem">${esc(u.message)}</div>` : ''}
                <div class="update-meta">${timeAgo(u.created_at)}</div>
              </div>
            </div>`).join('')}
        </div>` : ''}
      `;
      document.getElementById('modalUpdateStatus').value   = complaint.status;
      document.getElementById('modalUpdatePriority').value = complaint.priority || 'medium';
      document.getElementById('modalAdminRemarks').value   = '';
      openModal('complaintModal');
    } catch (err) { showToast(err.message, 'error'); }
  }

  document.querySelectorAll('#complaintModal .close').forEach(btn =>
    btn.addEventListener('click', () => closeModal('complaintModal')));
  document.getElementById('complaintModal')?.addEventListener('click', e => {
    if (e.target === e.currentTarget) closeModal('complaintModal');
  });

  document.getElementById('modalUpdateForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    const msg = document.getElementById('modalUpdateMessage');
    try {
      await api.put(`/complaints/${activeComplaintId}/update`, {
        status:        document.getElementById('modalUpdateStatus').value,
        priority:      document.getElementById('modalUpdatePriority').value,
        admin_remarks: document.getElementById('modalAdminRemarks').value.trim(),
      });
      msg.textContent = '✅ Updated successfully!';
      msg.className = 'form-message success'; msg.style.display = 'block';
      showToast('Complaint updated!', 'success');
      setTimeout(() => { closeModal('complaintModal'); loadDashboard(); loadAllComplaints(); }, 700);
    } catch (err) {
      msg.textContent = err.message;
      msg.className = 'form-message error'; msg.style.display = 'block';
    } finally { btn.disabled = false; }
  });

  document.getElementById('deleteComplaintBtn')?.addEventListener('click', async () => {
    if (!confirm('Delete this complaint permanently?')) return;
    try {
      await api.delete(`/complaints/${activeComplaintId}`);
      showToast('Complaint deleted.', 'success');
      closeModal('complaintModal');
      loadDashboard(); loadAllComplaints();
    } catch (err) { showToast(err.message, 'error'); }
  });

  // ── User Management ──────────────────────────────────────
  let allUsers = [];

  async function loadUsers(filters = {}, page = 1) {
    const container = document.getElementById('usersList');
    if (!container) return;
    try {
      const search    = document.getElementById('userSearchInput')?.value.trim() || '';
      const user_type = document.getElementById('userTypeFilter')?.value || '';
      const { users, pagination } = await api.get('/users', { search, user_type, page, per_page: 15, ...filters });
      allUsers = users;
      renderUsersTable(users);
    } catch (err) { showToast(err.message, 'error'); }
  }

  function renderUsersTable(users) {
    const container = document.getElementById('usersList');
    if (!users.length) {
      container.innerHTML = `<div class="empty-state"><div class="empty-icon">👥</div><p>No users found</p></div>`;
      return;
    }
    container.innerHTML = `
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>User ID</th><th>Full Name</th><th>Email</th><th>Type</th><th>Status</th><th>Created</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${users.map(u => `
              <tr>
                <td><code>${esc(u.user_id)}</code></td>
                <td>${esc(u.full_name)}</td>
                <td>${esc(u.email)}</td>
                <td><span class="badge badge-${esc(u.user_type)}">${esc(u.user_type)}</span></td>
                <td>${u.is_activated
                  ? '<span class="badge badge-resolved">Active</span>'
                  : '<span class="badge badge-pending">Pending</span>'}</td>
                <td>${timeAgo(u.created_at)}</td>
                <td>
                  <div class="table-actions">
                    <button class="btn btn-sm btn-secondary" onclick="editUser(${u.id}, ${JSON.stringify(u).replace(/"/g,'&quot;')})">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteUser(${u.id}, '${esc(u.full_name)}')">Delete</button>
                  </div>
                </td>
              </tr>`).join('')}
          </tbody>
        </table>
      </div>`;
  }

  let searchUsersDebounce = null;
  ['userSearchInput', 'userTypeFilter'].forEach(id => {
    document.getElementById(id)?.addEventListener('input', () => { clearTimeout(searchUsersDebounce); searchUsersDebounce = setTimeout(loadUsers, 400); });
    document.getElementById(id)?.addEventListener('change', () => loadUsers());
  });

  // Add User Modal
  document.getElementById('addUserBtn')?.addEventListener('click', () => {
    document.getElementById('addUserForm').reset();
    document.getElementById('addUserMessage').style.display = 'none';
    openModal('addUserModal');
  });
  document.querySelectorAll('#addUserModal .close').forEach(btn =>
    btn.addEventListener('click', () => closeModal('addUserModal')));

  document.getElementById('addUserForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    const msg = document.getElementById('addUserMessage');
    try {
      const data = await api.post('/users', {
        user_id:   document.getElementById('newUserId').value.trim(),
        full_name: document.getElementById('newUserName').value.trim(),
        email:     document.getElementById('newUserEmail').value.trim(),
        phone:     document.getElementById('newUserPhone').value.trim(),
        user_type: document.getElementById('newUserType').value,
        birthdate: document.getElementById('newUserBirthdate').value,
      });
      msg.innerHTML = `✅ ${data.message}<br><strong>Temp password:</strong> <code>${data.temp_password}</code>`;
      msg.className = 'form-message success'; msg.style.display = 'block';
      showToast('User created!', 'success');
      loadUsers();
    } catch (err) {
      msg.textContent = err.message;
      msg.className = 'form-message error'; msg.style.display = 'block';
    } finally { btn.disabled = false; }
  });

  // Edit / Delete user (exposed globally for table onclick)
  window.editUser = (id, userObj) => {
    document.getElementById('editUserId').value       = id;
    document.getElementById('editUserName').value     = userObj.full_name;
    document.getElementById('editUserEmail').value    = userObj.email;
    document.getElementById('editUserPhone').value    = userObj.phone || '';
    document.getElementById('editUserType').value     = userObj.user_type;
    document.getElementById('editUserMessage').style.display = 'none';
    openModal('editUserModal');
  };
  document.querySelectorAll('#editUserModal .close').forEach(btn =>
    btn.addEventListener('click', () => closeModal('editUserModal')));

  document.getElementById('editUserForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    const id  = document.getElementById('editUserId').value;
    const msg = document.getElementById('editUserMessage');
    try {
      await api.put(`/users/${id}`, {
        full_name: document.getElementById('editUserName').value.trim(),
        email:     document.getElementById('editUserEmail').value.trim(),
        phone:     document.getElementById('editUserPhone').value.trim(),
        user_type: document.getElementById('editUserType').value,
      });
      msg.textContent = 'User updated successfully.';
      msg.className = 'form-message success'; msg.style.display = 'block';
      showToast('User updated!', 'success');
      loadUsers();
      setTimeout(() => closeModal('editUserModal'), 1000);
    } catch (err) {
      msg.textContent = err.message;
      msg.className = 'form-message error'; msg.style.display = 'block';
    } finally { btn.disabled = false; }
  });

  window.deleteUser = async (id, name) => {
    if (!confirm(`Delete user "${name}"? This will also delete all their complaints.`)) return;
    try {
      await api.delete(`/users/${id}`);
      showToast(`User "${name}" deleted.`, 'success');
      loadUsers();
    } catch (err) { showToast(err.message, 'error'); }
  };

  // ── Reports ──────────────────────────────────────────────
  async function loadReports() {
    try {
      const { stats } = await api.get('/stats/dashboard');
      const totalC = stats.total_complaints || 0;
      const resolved = stats.by_status?.find(s => s.status === 'resolved')?.count || 0;
      const pending  = stats.by_status?.find(s => s.status === 'pending')?.count  || 0;
      document.getElementById('reportTotalComplaints').textContent   = totalC;
      document.getElementById('reportResolved').textContent          = resolved;
      document.getElementById('reportPending').textContent           = pending;
      document.getElementById('reportResolutionRate').textContent    = (stats.resolution_rate || 0) + '%';
      document.getElementById('reportAvgDays').textContent           = (stats.avg_resolution_days || 0) + ' days';
      document.getElementById('reportTotalUsers').textContent        = stats.total_users || 0;

      const colorMap = { academic:'#4f46e5', infrastructure:'#10b981', administrative:'#f59e0b',
                         technical:'#3b82f6', hostel:'#8b5cf6', transport:'#ef4444', other:'#94a3b8' };
      renderBarChart('reportCategoryChart', stats.by_category || [], 'category', 'count', c => colorMap[c]||'#94a3b8');
      renderBarChart('reportStatusChart',   stats.by_status   || [], 'status',   'count',
        s => ({ pending:'#f59e0b','in-progress':'#3b82f6',resolved:'#10b981',closed:'#94a3b8',rejected:'#ef4444' }[s]||'#94a3b8'));
      renderBarChart('reportPriorityChart', stats.by_priority || [], 'priority', 'count',
        p => ({ low:'#10b981', medium:'#f59e0b', high:'#f97316', urgent:'#ef4444' }[p]||'#94a3b8'));

      if (stats.monthly_trend?.length) {
        renderBarChart('reportMonthlyChart', stats.monthly_trend, 'month', 'count', () => '#4f46e5');
      }
    } catch (err) { showToast(err.message, 'error'); }
  }

  // ── Password change ──────────────────────────────────────
  document.getElementById('changePasswordForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const msg = document.getElementById('passwordMessage');
    const new_password = document.getElementById('newPassword').value;
    if (new_password !== document.getElementById('confirmNewPassword').value) {
      msg.textContent = 'Passwords do not match.'; msg.className = 'form-message error'; msg.style.display = 'block'; return;
    }
    try {
      const data = await api.post('/auth/reset-password', { old_password: document.getElementById('oldPassword').value, new_password });
      msg.textContent = data.message; msg.className = 'form-message success'; msg.style.display = 'block';
      e.target.reset();
    } catch (err) { msg.textContent = err.message; msg.className = 'form-message error'; msg.style.display = 'block'; }
  });

  // ── Initial load ─────────────────────────────────────────
  loadDashboard();
});
