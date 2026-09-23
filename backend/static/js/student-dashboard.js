/* ============================================================
   CMS - Student / Faculty Dashboard Script
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  const user = requireLogin();
  if (!user) return;
  if (!['student', 'faculty'].includes(user.user_type)) {
    window.location.href = '/login.html'; return;
  }

  // ── Populate header ──────────────────────────────────────
  document.getElementById('userName').textContent    = user.full_name;
  document.getElementById('userType').textContent    = user.user_type;
  document.getElementById('userType').className      = `badge badge-${user.user_type}`;
  document.getElementById('profileUserId').textContent = user.user_id;
  document.getElementById('profileName').textContent   = user.full_name;
  document.getElementById('profileEmail').textContent  = user.email || '—';
  document.getElementById('profileType').textContent   = user.user_type;

  // ── Sidebar navigation ───────────────────────────────────
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const page = link.dataset.page;
      document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
      link.classList.add('active');
      document.querySelectorAll('.page-content').forEach(p => p.classList.remove('active'));
      document.getElementById(pageIdMap[page])?.classList.add('active');
      if (page === 'complaints') loadMyComplaints();
      if (page === 'dashboard')  loadDashboard();
    });
  });

  const pageIdMap = {
    'dashboard':      'dashboardPage',
    'complaints':     'complaintsPage',
    'new-complaint':  'newComplaintPage',
    'profile':        'profilePage',
  };

  // ── Logout ───────────────────────────────────────────────
  document.getElementById('logoutBtn').addEventListener('click', () => {
    Auth.clear();
    window.location.href = '/login.html';
  });

  // ── Load dashboard stats ─────────────────────────────────
  async function loadDashboard() {
    try {
      const { stats } = await api.get('/stats/dashboard');
      document.getElementById('totalComplaints').textContent   = stats.my_complaints || 0;
      const pending  = stats.my_status?.find(s => s.status === 'pending')?.count     || 0;
      const progress = stats.my_status?.find(s => s.status === 'in-progress')?.count || 0;
      const resolved = stats.my_status?.find(s => s.status === 'resolved')?.count    || 0;
      document.getElementById('pendingComplaints').textContent    = pending;
      document.getElementById('inProgressComplaints').textContent = progress;
      document.getElementById('resolvedComplaints').textContent   = resolved;
      renderRecentComplaints(stats.recent || []);
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  function renderRecentComplaints(list) {
    const container = document.getElementById('recentComplaintsList');
    if (!list.length) {
      container.innerHTML = `<div class="empty-state"><div class="empty-icon">📭</div><p>No complaints yet</p></div>`;
      return;
    }
    container.innerHTML = list.map(c => complaintCard(c)).join('');
    container.querySelectorAll('.complaint-card').forEach(card => {
      card.addEventListener('click', () => openComplaintDetails(card.dataset.id));
    });
  }

  // ── Load my complaints ───────────────────────────────────
  let allComplaints = [];
  async function loadMyComplaints() {
    try {
      const { complaints } = await api.get('/complaints/my');
      allComplaints = complaints;
      renderComplaints(complaints);
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  document.getElementById('statusFilter')?.addEventListener('change', (e) => {
    const val = e.target.value;
    const filtered = val ? allComplaints.filter(c => c.status === val) : allComplaints;
    renderComplaints(filtered);
  });

  function renderComplaints(list) {
    const container = document.getElementById('complaintsList');
    if (!list.length) {
      container.innerHTML = `<div class="empty-state"><div class="empty-icon">📭</div><p>No complaints found</p></div>`;
      return;
    }
    container.innerHTML = list.map(c => complaintCard(c)).join('');
    container.querySelectorAll('.complaint-card').forEach(card => {
      card.addEventListener('click', () => openComplaintDetails(card.dataset.id));
    });
  }

  function complaintCard(c) {
    return `
      <div class="complaint-card" data-id="${esc(c.complaint_id)}">
        <div class="complaint-card-header">
          <div>
            <div class="complaint-title">${esc(c.title)}</div>
            <div class="complaint-meta">
              <span class="complaint-id">${esc(c.complaint_id)}</span>
              <span>${esc(c.category)}</span>
              <span>${timeAgo(c.created_at)}</span>
            </div>
          </div>
          <div style="display:flex;gap:6px;flex-shrink:0">
            ${statusBadge(c.status)}
            ${priorityBadge(c.priority || 'medium')}
          </div>
        </div>
        <div class="complaint-description">${esc(c.description)}</div>
      </div>`;
  }

  // ── Open complaint details modal ─────────────────────────
  async function openComplaintDetails(complaintId) {
    try {
      const { complaint } = await api.get(`/complaints/${complaintId}`);
      const details = document.getElementById('complaintDetails');
      details.innerHTML = `
        <div class="complaint-details-grid">
          <div class="detail-item">
            <label>Complaint ID</label>
            <code>${esc(complaint.complaint_id)}</code>
          </div>
          <div class="detail-item">
            <label>Status</label>
            ${statusBadge(complaint.status)}
          </div>
          <div class="detail-item">
            <label>Category</label>
            <span>${esc(complaint.category)}</span>
          </div>
          <div class="detail-item">
            <label>Priority</label>
            ${priorityBadge(complaint.priority || 'medium')}
          </div>
          <div class="detail-item detail-full">
            <label>Title</label>
            <strong>${esc(complaint.title)}</strong>
          </div>
          <div class="detail-item detail-full">
            <label>Description</label>
            <p style="white-space:pre-wrap">${esc(complaint.description)}</p>
          </div>
          ${complaint.admin_remarks ? `
          <div class="detail-item detail-full">
            <label>Admin Remarks</label>
            <p>${esc(complaint.admin_remarks)}</p>
          </div>` : ''}
          ${complaint.attachment_path ? `
          <div class="detail-item detail-full">
            <label>Attachment</label>
            <a href="/api/uploads/${esc(complaint.attachment_path)}" target="_blank" class="btn btn-sm btn-secondary">📎 View Attachment</a>
          </div>` : ''}
          <div class="detail-item">
            <label>Submitted</label>
            <span>${formatDate(complaint.created_at)}</span>
          </div>
          ${complaint.resolved_at ? `
          <div class="detail-item">
            <label>Resolved At</label>
            <span>${formatDate(complaint.resolved_at)}</span>
          </div>` : ''}
        </div>

        ${complaint.updates?.length ? `
        <div class="updates-timeline">
          <h4 style="margin-bottom:10px">Activity Log</h4>
          ${complaint.updates.map(u => `
            <div class="update-item">
              <div class="update-dot"></div>
              <div class="update-content">
                <div><strong>${esc(u.updated_by_name)}</strong>
                  ${u.update_type === 'status_change'
                    ? ` changed status: ${statusBadge(u.old_status)} → ${statusBadge(u.new_status)}`
                    : ` added a comment`}
                </div>
                ${u.message ? `<div style="color:var(--text-secondary);font-size:.85rem">${esc(u.message)}</div>` : ''}
                <div class="update-meta">${timeAgo(u.created_at)}</div>
              </div>
            </div>`).join('')}
        </div>` : ''}
      `;
      openModal('complaintModal');
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  // Close modal
  document.querySelector('.close')?.addEventListener('click', () => closeModal('complaintModal'));
  document.getElementById('complaintModal')?.addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeModal('complaintModal');
  });

  // ── New Complaint Form ───────────────────────────────────
  const newComplaintForm = document.getElementById('newComplaintForm');
  const formMessage = document.getElementById('formMessage');

  // ── ML Predictions ──────────────────────────────────────
  const mlPanel = document.getElementById('mlPanel');
  let mlDebounce = null;
  let mlLastText  = '';

  function triggerML() {
    clearTimeout(mlDebounce);
    mlDebounce = setTimeout(fetchMLSuggestions, 900);
  }

  document.getElementById('title')?.addEventListener('input', triggerML);
  document.getElementById('description')?.addEventListener('input', triggerML);

  async function fetchMLSuggestions() {
    const title       = (document.getElementById('title')?.value       || '').trim();
    const description = (document.getElementById('description')?.value || '').trim();
    const combined    = title + ' ' + description;

    // Need at least 8 chars to be meaningful
    if (combined.trim().length < 8) {
      hideMlPanel(); return;
    }
    // Skip if text hasn't changed
    if (combined === mlLastText) return;
    mlLastText = combined;

    const category = document.getElementById('category')?.value || '';

    // Show loading state
    showMlLoading();

    try {
      const resp = await fetch('/api/ml/analyze-all', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + (Auth.getToken() || '')
        },
        body: JSON.stringify({ title, description, category })
      });

      if (!resp.ok) { hideMlPanel(); return; }
      const data = await resp.json();

      if (!data.success || !data.analysis) { hideMlPanel(); return; }
      renderMLPanel(data.analysis);
    } catch (err) {
      hideMlPanel();
    }
  }

  function hideMlPanel() {
    if (mlPanel) { mlPanel.style.display = 'none'; mlPanel.innerHTML = ''; }
  }

  function showMlLoading() {
    if (!mlPanel) return;
    mlPanel.style.display = 'flex';
    mlPanel.innerHTML = `
      <div style="background:var(--primary-bg);border:1px solid var(--primary-light);
                  border-radius:var(--radius);padding:10px 14px;font-size:.85rem;
                  color:var(--primary);display:flex;align-items:center;gap:8px">
        <div class="spinner" style="width:16px;height:16px;border-width:2px"></div>
        Analysing complaint with AI…
      </div>`;
  }

  function renderMLPanel(analysis) {
    if (!mlPanel) return;
    let html = '';

    // ── 1. Category suggestion ────────────────────────────
    const cat = analysis.category;
    if (cat && cat.category) {
      const conf = Math.round((cat.confidence || 0) * 100);
      const chipsHtml = (cat.top_3 || []).map(t =>
        `<span class="ml-chip" data-cat="${esc(t.category)}">
           ${esc(t.category)}
           <small style="opacity:.65">${Math.round((t.confidence||0)*100)}%</small>
         </span>`
      ).join('');

      html += `
        <div style="background:var(--primary-bg);border:1px solid var(--primary-light);
                    border-radius:var(--radius);padding:12px 14px">
          <div style="font-size:.85rem;margin-bottom:6px">
            🤖 <strong>AI Category:</strong>
            <span style="color:var(--primary);font-weight:600;text-transform:capitalize">
              ${esc(cat.category)}
            </span>
            <span style="color:var(--text-muted);font-size:.78rem">&nbsp;(${conf}% confidence)</span>
          </div>
          <div class="ml-chips">${chipsHtml}</div>
          <div style="font-size:.73rem;color:var(--text-muted);margin-top:5px">
            💡 Click a chip to apply the category automatically
          </div>
        </div>`;
    }

    // ── 2. Priority suggestion ────────────────────────────
    const pri = analysis.priority;
    if (pri && pri.priority) {
      const conf = Math.round((pri.confidence || 0) * 100);
      const bgMap    = { urgent:'#fef2f2', high:'#fff7ed', medium:'#fefce8', low:'#f0fdf4' };
      const borderMap= { urgent:'#fca5a5', high:'#fdba74', medium:'#fde047', low:'#86efac' };
      const bg  = bgMap[pri.priority]    || '#fdf4ff';
      const bdr = borderMap[pri.priority]|| '#d8b4fe';
      html += `
        <div style="background:${bg};border:1px solid ${bdr};
                    border-radius:var(--radius);padding:12px 14px">
          <div style="font-size:.85rem">
            ⚡ <strong>Suggested Priority:</strong>
            ${priorityBadge(pri.priority)}
            <span style="color:var(--text-muted);font-size:.78rem">&nbsp;(${conf}% confidence)</span>
          </div>
          ${pri.reasoning
            ? `<div style="font-size:.78rem;color:var(--text-secondary);margin-top:4px">${esc(pri.reasoning)}</div>`
            : ''}
        </div>`;
    }

    // ── 3. Sentiment analysis ─────────────────────────────
    const sent = analysis.sentiment;
    if (sent && sent.sentiment) {
      const urg    = sent.urgency_indicator || 'normal';
      const bgMap  = { critical:'#fef2f2', high:'#fff7ed', medium:'#fefce8', normal:'#f0fdf4' };
      const bdrMap = { critical:'#fca5a5', high:'#fdba74', medium:'#fde047', normal:'#86efac' };
      const score  = sent.satisfaction_score !== undefined ? sent.satisfaction_score : null;
      html += `
        <div style="background:${bgMap[urg]||'#fefce8'};border:1px solid ${bdrMap[urg]||'#fde047'};
                    border-radius:var(--radius);padding:12px 14px">
          <div style="font-size:.85rem">
            ${sent.emoji || '😐'} <strong>Sentiment:</strong>
            <span style="text-transform:capitalize">${esc((sent.sentiment||'').replace(/_/g,' '))}</span>
            &nbsp;·&nbsp; <strong>Emotion:</strong>
            <span style="text-transform:capitalize">${esc(sent.emotion || 'neutral')}</span>
            &nbsp;·&nbsp; <strong>Urgency:</strong>
            <span style="text-transform:capitalize">${esc(urg)}</span>
            ${score !== null
              ? `&nbsp;·&nbsp; <strong>Satisfaction:</strong> ${score}/100`
              : ''}
          </div>
          ${sent.recommendation
            ? `<div style="font-size:.78rem;color:var(--text-secondary);margin-top:4px">${esc(sent.recommendation)}</div>`
            : ''}
        </div>`;
    }

    // ── 4. Resolution time ────────────────────────────────
    const res = analysis.resolution_time;
    if (res && res.time_estimate) {
      const factorsHtml = (res.factors || []).length
        ? `<ul style="margin:4px 0 0 14px;font-size:.76rem;color:var(--text-secondary)">
             ${res.factors.map(f => `<li>${esc(f)}</li>`).join('')}
           </ul>`
        : '';
      html += `
        <div style="background:#f0fdf4;border:1px solid #86efac;
                    border-radius:var(--radius);padding:12px 14px">
          <div style="font-size:.85rem">
            ⏱ <strong>Estimated Resolution:</strong>
            <span style="color:var(--success);font-weight:600">${esc(res.time_estimate)}</span>
            ${res.range
              ? `<span style="color:var(--text-muted);font-size:.78rem">
                   &nbsp;(${res.range.min_hours}h – ${res.range.max_hours}h range)
                 </span>`
              : ''}
            ${res.estimated_resolution_date
              ? `<span style="color:var(--text-muted);font-size:.78rem">
                   &nbsp;· by ${esc(res.estimated_resolution_date)}
                 </span>`
              : ''}
          </div>
          ${factorsHtml}
        </div>`;
    }

    if (!html) { hideMlPanel(); return; }

    mlPanel.style.display = 'flex';
    mlPanel.innerHTML = html;

    // Wire up category chips
    mlPanel.querySelectorAll('.ml-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const val = chip.dataset.cat;
        const sel = document.getElementById('category');
        if (sel && val) {
          sel.value = val;
          mlPanel.querySelectorAll('.ml-chip').forEach(c => c.classList.remove('active'));
          chip.classList.add('active');
          // Refresh with new category
          mlLastText = '';
          clearTimeout(mlDebounce);
          mlDebounce = setTimeout(fetchMLSuggestions, 200);
        }
      });
    });
  }

    newComplaintForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = newComplaintForm.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = 'Submitting…';
    formMessage.className = 'form-message';
    formMessage.style.display = 'none';

    const fd = new FormData(newComplaintForm);

    try {
      const data = await api.postForm('/complaints', fd);
      formMessage.textContent = `✅ ${data.message} — ID: ${data.complaint_id}`;
      formMessage.className = 'form-message success';
      formMessage.style.display = 'block';
      newComplaintForm.reset();
      document.getElementById('mlSuggestionsContainer')?.remove();
      showToast('Complaint submitted successfully!', 'success');
      loadDashboard();
    } catch (err) {
      formMessage.textContent = err.message;
      formMessage.className = 'form-message error';
      formMessage.style.display = 'block';
    } finally {
      btn.disabled = false;
      btn.textContent = 'Submit Complaint';
    }
  });

  // ── Change password ──────────────────────────────────────
  document.getElementById('changePasswordForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const old_password  = document.getElementById('oldPassword').value;
    const new_password  = document.getElementById('newPassword').value;
    const confirm       = document.getElementById('confirmNewPassword').value;
    const msg           = document.getElementById('passwordMessage');

    if (new_password !== confirm) {
      msg.textContent = 'New passwords do not match.';
      msg.className = 'form-message error';
      msg.style.display = 'block';
      return;
    }
    try {
      const data = await api.post('/auth/reset-password', { old_password, new_password });
      msg.textContent = data.message;
      msg.className = 'form-message success';
      msg.style.display = 'block';
      e.target.reset();
    } catch (err) {
      msg.textContent = err.message;
      msg.className = 'form-message error';
      msg.style.display = 'block';
    }
  });

  // ── Initial load ─────────────────────────────────────────
  loadDashboard();
});
