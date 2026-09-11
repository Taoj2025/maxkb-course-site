/**
 * MaxKB 管理后台 · v2 (2026-09-11)
 * 改动：完全去掉 localStorage 假数据，调用 /api/admin/* 真实数据
 */

(function () {
  let currentPage = 1;
  let currentPageSize = 20;
  let currentQuery = '';

  // ============ 管理员登录 ============
  function showLogin() {
    document.getElementById('login-panel').style.display = 'flex';
    document.getElementById('admin-panel').style.display = 'none';
  }

  function showAdmin() {
    document.getElementById('login-panel').style.display = 'none';
    document.getElementById('admin-panel').style.display = 'block';
  }

  async function doLogin() {
    const email = document.getElementById('admin-email').value.trim();
    const password = document.getElementById('admin-password').value;
    const errorEl = document.getElementById('admin-error');
    errorEl.textContent = '';

    if (!email || !password) {
      errorEl.textContent = '请输入邮箱和密码';
      return;
    }

    try {
      const r = await window.api.login(email, password);
      if (r.user.role !== 'admin') {
        errorEl.textContent = '⚠️ 该账号不是管理员（role=' + r.user.role + '）';
        window.api.logout();
        return;
      }
      showAdmin();
      await Promise.all([loadStats(), loadUsers(), loadLogs()]);
    } catch (e) {
      errorEl.textContent = '登录失败：' + (e.message || e);
    }
  }

  // ============ 数据看板 ============
  async function loadStats() {
    try {
      const s = await window.api.adminStats();
      document.getElementById('stat-total').textContent     = s.total_users || 0;
      document.getElementById('stat-standard').textContent  = (s.plan_distribution && s.plan_distribution.standard) || 0;
      document.getElementById('stat-flagship').textContent  = (s.plan_distribution && s.plan_distribution.flagship) || 0;
      document.getElementById('stat-free').textContent      = (s.plan_distribution && s.plan_distribution.free) || 0;
      document.getElementById('stat-downloads').textContent = s.total_downloads || 0;
      document.getElementById('stat-revenue').textContent   = '¥' + (s.estimated_revenue_yuan || 0);
      document.getElementById('stat-messages').textContent  = s.new_messages || 0;
      document.getElementById('stat-articles').textContent  = s.published_articles || 0;
    } catch (e) {
      console.error('loadStats failed:', e);
    }
  }

  // ============ 用户列表 ============
  async function loadUsers(page = 1) {
    currentPage = page;
    try {
      const r = await window.api.adminUsers({ page, size: currentPageSize, q: currentQuery });
      renderUserTable(r.items);
      renderPagination(r.total, page);
    } catch (e) {
      console.error('loadUsers failed:', e);
      if (e.status === 401 || e.status === 403) {
        showLogin();
      }
    }
  }

  function renderUserTable(items) {
    const tbody = document.getElementById('user-tbody');
    if (!tbody) return;

    if (!items.length) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 24px; color: var(--gray);">暂无用户</td></tr>';
      return;
    }

    const planColor = { 'free': '#94A3B8', 'standard': '#8B5CF6', 'flagship': '#5B2EBF' };
    const statusColor = { 'active': '#34D399', 'expired': '#F59E0B', 'banned': '#EF4444' };

    tbody.innerHTML = items.map(u => `
      <tr>
        <td><strong>${escapeHtml(u.email)}</strong>${u.role === 'admin' ? ' 👑' : ''}</td>
        <td><span class="plan-badge" style="background:${planColor[u.plan_id]};">${planName(u.plan_id)}</span></td>
        <td><span class="status-badge" style="background:${statusColor[u.status]};">${u.status}</span></td>
        <td>${formatDate(u.joined_at)}</td>
        <td>${u.upgraded_at ? formatDate(u.upgraded_at) : '—'}</td>
        <td>${u.expires_at ? formatDate(u.expires_at) : '—'}</td>
        <td>${u.total_downloads || 0}</td>
        <td class="actions">
          <button onclick="window.MAXKB_ADMIN.upgrade('${u.id}', 'standard')" class="btn-mini btn-standard">升标准</button>
          <button onclick="window.MAXKB_ADMIN.upgrade('${u.id}', 'flagship')" class="btn-mini btn-flagship">升旗舰</button>
          <button onclick="window.MAXKB_ADMIN.downgrade('${u.id}')" class="btn-mini">降免费</button>
          ${u.status === 'banned'
            ? `<button onclick="window.MAXKB_ADMIN.unban('${u.id}')" class="btn-mini btn-success">解封</button>`
            : `<button onclick="window.MAXKB_ADMIN.ban('${u.id}')" class="btn-mini btn-danger">封禁</button>`
          }
        </td>
      </tr>
    `).join('');
  }

  function renderPagination(total, page) {
    const totalPages = Math.max(1, Math.ceil(total / currentPageSize));
    const pg = document.getElementById('pagination');
    if (!pg) return;
    pg.innerHTML = `
      <span style="color:var(--gray);">共 ${total} 条 / 第 ${page} / ${totalPages} 页</span>
      <button onclick="window.MAXKB_ADMIN.loadUsers(${page - 1})" ${page <= 1 ? 'disabled' : ''} class="btn-mini">上一页</button>
      <button onclick="window.MAXKB_ADMIN.loadUsers(${page + 1})" ${page >= totalPages ? 'disabled' : ''} class="btn-mini">下一页</button>
    `;
  }

  // ============ 操作 ============
  async function upgrade(id, plan) {
    const user = currentUserList.find(u => u.id === id);
    if (!user) return alert('用户不存在');
    if (!confirm(`确认将 ${user.email} 升级到 ${planName(plan)}？`)) return;
    try {
      await window.api.adminUpgrade(id, plan);
      alert('✅ 已升级');
      await Promise.all([loadStats(), loadUsers(currentPage)]);
    } catch (e) {
      alert('升级失败：' + e.message);
    }
  }

  async function downgrade(id) {
    const user = currentUserList.find(u => u.id === id);
    if (!user) return alert('用户不存在');
    if (!confirm(`确认将 ${user.email} 降级到免费会员？`)) return;
    try {
      await window.api.adminDowngrade(id);
      alert('✅ 已降级');
      await Promise.all([loadStats(), loadUsers(currentPage)]);
    } catch (e) {
      alert('降级失败：' + e.message);
    }
  }

  async function ban(id) {
    const user = currentUserList.find(u => u.id === id);
    if (!user) return alert('用户不存在');
    if (!confirm(`确认封禁 ${user.email}？封禁后无法登录。`)) return;
    try {
      await window.api.adminBan(id);
      alert('✅ 已封禁');
      await loadUsers(currentPage);
    } catch (e) {
      alert('封禁失败：' + e.message);
    }
  }

  async function unban(id) {
    try {
      await window.api.adminUnban(id);
      alert('✅ 已解封');
      await loadUsers(currentPage);
    } catch (e) {
      alert('解封失败：' + e.message);
    }
  }

  async function doSearch() {
    currentQuery = document.getElementById('search-input').value.trim();
    await loadUsers(1);
  }

  async function exportCSV() {
    try {
      const r = await window.api.adminUsers({ size: 1000, q: currentQuery });
      const rows = [['邮箱', '套餐', '状态', '注册时间', '升级时间', '到期时间', '下载数', '角色']];
      r.items.forEach(u => rows.push([
        u.email, u.plan_id, u.status, u.joined_at, u.upgraded_at || '', u.expires_at || '',
        u.total_downloads || 0, u.role || 'user'
      ]));
      const csv = '﻿' + rows.map(row => row.map(cell => `"${String(cell || '').replace(/"/g, '""')}"`).join(',')).join('\n');
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = 'maxkb_users_' + new Date().toISOString().slice(0, 10) + '.csv';
      a.click(); URL.revokeObjectURL(url);
    } catch (e) {
      alert('导出失败：' + e.message);
    }
  }

  async function loadLogs() {
    try {
      const r = await window.api.adminLogs(20);
      const tbody = document.getElementById('logs-tbody');
      if (!tbody) return;
      tbody.innerHTML = r.items.map(l => `
        <tr>
          <td>${formatDate(l.created_at)}</td>
          <td>${escapeHtml(l.admin_email)}</td>
          <td><code>${escapeHtml(l.action)}</code></td>
          <td>${l.target_id || '—'}</td>
          <td><code style="font-size:11px;">${escapeHtml(JSON.stringify(l.details || {}))}</code></td>
        </tr>
      `).join('') || '<tr><td colspan="5" style="text-align:center; padding: 16px; color: var(--gray);">暂无操作日志</td></tr>';
    } catch (e) {
      console.error('loadLogs failed:', e);
    }
  }

  async function refreshAll() {
    await Promise.all([loadStats(), loadUsers(currentPage), loadLogs()]);
  }

  // ============ 工具 ============
  let currentUserList = [];

  const _origRender = renderUserTable;
  renderUserTable = function (items) { currentUserList = items; _origRender(items); };

  function formatDate(d) {
    if (!d) return '—';
    const dt = new Date(d);
    if (isNaN(dt)) return d;
    return dt.toISOString().slice(0, 16).replace('T', ' ');
  }

  function escapeHtml(s) {
    return String(s || '').replace(/[&<>"']/g, c => ({ '&': '&', '<': '<', '>': '>', '"': '"', "'": '&#39;' }[c]));
  }

  function planName(id) {
    return ({ 'free': '体验', 'standard': '标准 ¥99', 'flagship': '旗舰 ¥299' })[id] || id;
  }

  // ============ 初始化 ============
  document.addEventListener('DOMContentLoaded', async () => {
    // 检查是否已登录 + 是 admin
    if (window.MAXKB_API_TOKEN.get()) {
      try {
        const r = await window.api.me();
        window.MAXKB_API_USER.set(r.user);
        if (r.user.role === 'admin') {
          showAdmin();
          await refreshAll();
        } else {
          showLogin();
          document.getElementById('admin-error').textContent = '⚠️ 当前账号 ' + r.user.email + ' 不是管理员';
          window.api.logout();
        }
      } catch (e) {
        showLogin();
      }
    } else {
      showLogin();
    }

    // 绑定登录按钮
    const loginBtn = document.getElementById('admin-login-btn');
    if (loginBtn) loginBtn.addEventListener('click', doLogin);
    const pwdInput = document.getElementById('admin-password');
    if (pwdInput) pwdInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') doLogin(); });

    // 刷新按钮
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) refreshBtn.addEventListener('click', refreshAll);

    // 搜索
    const searchBtn = document.getElementById('search-btn');
    if (searchBtn) searchBtn.addEventListener('click', doSearch);
    const searchInput = document.getElementById('search-input');
    if (searchInput) searchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') doSearch(); });

    // 导出
    const exportBtn = document.getElementById('export-btn');
    if (exportBtn) exportBtn.addEventListener('click', exportCSV);

    // 登出
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) logoutBtn.addEventListener('click', () => {
      window.api.logout(); showLogin();
    });
  });

  // 暴露给 HTML 内嵌按钮调用
  window.MAXKB_ADMIN = {
    loadUsers, upgrade, downgrade, ban, unban, exportCSV, doSearch, loadStats, loadLogs, refreshAll,
  };
})();
