/**
 * MaxKB 前端配置
 *
 * ⚠️ API_BASE 是「站点根」，不是「API 根」。
 *    api.js 里 apiFetch 传的路径自带 /api 前缀（apiFetch('/api/articles')），
 *    所以 base 不能带 /api —— 否则拼出来是 /api/api/articles，直接 404。
 *    （之前就是这里写成了 'https://taotaoedu.ltd/api'，全站接口调用从 v2.0 起就没通过。）
 *
 * 取值策略（三种部署都能跑，不用手工改）：
 *   '' → 同源。
 *        - Nginx 部署：location /api/ 反代到 127.0.0.1:3001
 *        - Vercel 部署：api/[...path].js 转发到源站
 *        同源请求浏览器不触发 CORS，也不用管白名单。
 *   'https://taotaoedu.ltd' → 兜底。
 *        GitHub Pages 这类纯静态托管没有 /api，只能跨域直连源站
 *        （源站 CORS 白名单里有 https://taoj2025.github.io）。
 *
 * api.js 会先探一次 /api/health 自动在两者之间选，探明后缓存在内存里。
 */
window.MAXKB_CONFIG = {
  // 生产环境：同源优先（空串 = 用当前页面的协议+域名）
  API_BASE: '',

  // 同源没有 /api 时退回源站绝对地址（跨域，源站 CORS 白名单已放行）
  API_BASE_FALLBACK: 'https://taotaoedu.ltd',

  // 后端不可达时的静态回退
  FALLBACK_ARTICLES:  'articles.json',
  FALLBACK_CHAPTERS: 'assets/js/data.js',   // 内置 chapters 数组
  FALLBACK_AIHOT:     'data/aihot.json',
  FALLBACK_RESOURCES: null,                  // 资源没有静态 fallback，必须登录鉴权

  // 调试开关（生产可改 false）
  DEBUG: false,
};
