/**
 * MaxKB 前端 API 封装
 * - 统一注入 JWT token
 * - 统一错误处理（401 自动清除 token）
 * - 统一 timeout（10s）
 * - 后端不可达时抛出 ApiUnreachableError（前端可 fallback）
 */

const TOKEN_KEY = 'maxkb_token';
const USER_CACHE_KEY = 'maxkb_user_cache';

function getToken()    { try { return localStorage.getItem(TOKEN_KEY); } catch { return null; } }
function setToken(t)   { try { localStorage.setItem(TOKEN_KEY, t); } catch {} }
function clearToken()  { try { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_CACHE_KEY); } catch {} }
function getCachedUser(){ try { return JSON.parse(localStorage.getItem(USER_CACHE_KEY) || 'null'); } catch { return null; } }
function setCachedUser(u){ try { localStorage.setItem(USER_CACHE_KEY, JSON.stringify(u)); } catch {} }

class ApiError extends Error {
  constructor(message, status, body) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

async function apiFetch(path, opts = {}) {
  const base = (window.MAXKB_CONFIG && window.MAXKB_CONFIG.API_BASE) || '';
  const url = base + path;
  const headers = {
    'Content-Type': 'application/json',
    ...(opts.headers || {}),
  };
  const token = getToken();
  if (token) headers.Authorization = 'Bearer ' + token;

  // 简单 timeout
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);

  let res;
  try {
    res = await fetch(url, { ...opts, headers, signal: controller.signal });
  } catch (e) {
    clearTimeout(timeout);
    throw new ApiError('网络错误或后端不可达', 0, { networkError: true });
  }
  clearTimeout(timeout);

  if (res.status === 401) {
    clearToken();
    // 触发登录状态条更新
    document.dispatchEvent(new CustomEvent('maxkb:auth:logout'));
  }

  let body = null;
  try { body = await res.json(); } catch { body = null; }

  if (!res.ok) {
    throw new ApiError((body && body.error) || `HTTP ${res.status}`, res.status, body);
  }
  return body;
}

const api = {
  // ============ Auth ============
  register: (email, password) =>
    apiFetch('/api/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) }),

  login: (email, password) =>
    apiFetch('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),

  me: () => apiFetch('/api/auth/me'),

  logout: () => { clearToken(); document.dispatchEvent(new CustomEvent('maxkb:auth:logout')); },

  // ============ 内容 ============
  articles: (q = {}) => {
    const qs = Object.keys(q).length ? '?' + new URLSearchParams(q).toString() : '';
    return apiFetch('/api/articles' + qs);
  },

  article: (slug) => apiFetch('/api/articles/' + encodeURIComponent(slug)),

  chapters: () => apiFetch('/api/chapters'),

  aihot: (category = 'general') => apiFetch('/api/aihot?category=' + encodeURIComponent(category)),

  resources: () => apiFetch('/api/resources'),

  // ============ 联系表单 ============
  contact: (data) =>
    apiFetch('/api/contact', { method: 'POST', body: JSON.stringify(data) }),

  // ============ 下载 ============
  downloadUrl: (slug) => {
    const base = (window.MAXKB_CONFIG && window.MAXKB_CONFIG.API_BASE) || '';
    return base + '/api/download/' + encodeURIComponent(slug);
  },

  /**
   * 触发下载（带 token）。返回 { ok, reason, requiredPlan, filename }
   */
  async download(slug) {
    const token = getToken();
    if (!token) return { ok: false, reason: 'not_logged_in' };

    const base = (window.MAXKB_CONFIG && window.MAXKB_CONFIG.API_BASE) || '';
    try {
      const res = await fetch(base + '/api/download/' + encodeURIComponent(slug), {
        headers: { Authorization: 'Bearer ' + token },
      });
      if (res.status === 401) { clearToken(); return { ok: false, reason: 'token_expired' }; }
      if (res.status === 402) {
        const body = await res.json().catch(() => ({}));
        return { ok: false, reason: 'upgrade_needed', requiredPlan: body.required_plan };
      }
      if (!res.ok) return { ok: false, reason: 'http_' + res.status };

      const blob = await res.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = slug;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(a.href);
      return { ok: true };
    } catch (e) {
      return { ok: false, reason: 'network_error' };
    }
  },

  // ============ Admin ============
  adminUsers: (q = {}) =>
    apiFetch('/api/admin/users?' + new URLSearchParams(q).toString()),

  adminUpgrade: (id, plan) =>
    apiFetch(`/api/admin/users/${id}/upgrade`, { method: 'POST', body: JSON.stringify({ plan }) }),

  adminDowngrade: (id) =>
    apiFetch(`/api/admin/users/${id}/downgrade`, { method: 'POST' }),

  adminBan: (id) =>
    apiFetch(`/api/admin/users/${id}/ban`, { method: 'POST' }),

  adminUnban: (id) =>
    apiFetch(`/api/admin/users/${id}/unban`, { method: 'POST' }),

  adminStats: () => apiFetch('/api/admin/stats'),

  adminLogs: (limit = 50) =>
    apiFetch(`/api/admin/logs?limit=${limit}`),
};

window.api = api;
window.MAXKB_API = api;
window.MAXKB_API_TOKEN = { get: getToken, set: setToken, clear: clearToken };
window.MAXKB_API_USER  = { get: getCachedUser, set: setCachedUser };
