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

// ── API 基址自适应 ──
//
// 同源优先，探不通再退回源站绝对地址：
//   Nginx 部署  → 同源 /api 有反代，能探通 → 用同源（不触发 CORS）
//   Vercel 部署 → 同源 /api 有函数转发，能探通 → 用同源
//   GitHub Pages → 同源没有 /api，探不通 → 退回绝对地址跨域直连源站
//
// 探路请求只发一次（GET /api/health），结果缓存在内存里。
// 不用在 POST 上做「失败重试」—— 那会导致注册/提交被发两遍。
let apiBaseResolved = null;
let apiBasePromise = null;

async function resolveApiBase() {
  if (apiBaseResolved !== null) return apiBaseResolved;
  if (apiBasePromise) return apiBasePromise;

  const cfg = window.MAXKB_CONFIG || {};
  const primary = cfg.API_BASE || '';
  const fallback = cfg.API_BASE_FALLBACK || '';

  // 没配兜底地址就不用探了
  if (!fallback || fallback === primary) {
    apiBaseResolved = primary;
    return primary;
  }

  apiBasePromise = (async () => {
    try {
      const res = await fetch(primary + '/api/health', { method: 'GET', cache: 'no-store' });
      if (res.ok) {
        apiBaseResolved = primary;
        return primary;
      }
    } catch (e) {
      // 网络错误 → 换兜底
    }
    apiBaseResolved = fallback;
    return fallback;
  })();
  return apiBasePromise;
}

async function apiFetch(path, opts = {}) {
  const base = await resolveApiBase();
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
    const cfg = window.MAXKB_CONFIG || {};
    // 还没探明就先给同源地址（探路在页面加载时就跑，通常已经探好了）
    const base = apiBaseResolved !== null ? apiBaseResolved : (cfg.API_BASE || '');
    return base + '/api/download/' + encodeURIComponent(slug);
  },

  /**
   * 触发下载（带 token）。返回 { ok, reason, requiredPlan, filename }
   */
  async download(slug) {
    const token = getToken();
    if (!token) return { ok: false, reason: 'not_logged_in' };

    const base = await resolveApiBase();
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

// 页面加载就把 API 基址探明，等首个真实请求时就不用再等了
resolveApiBase().catch(() => {});
