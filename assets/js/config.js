/**
 * MaxKB 前端配置
 * 用户部署后端后，把 API_BASE 改为真实地址，例如：
 *   - https://api.maxkb-edu.com （子域名反代）
 *   - https://maxkb-edu.com/api （同源路径反代，Nginx 推荐）
 *   - http://localhost:3001 （本地调试）
 *
 * Fallback 路径：后端不可达时使用，保证前端永不白屏
 */
window.MAXKB_CONFIG = {
  // 生产环境：Nginx 反代 · https://maxkb-edu.com/api → 127.0.0.1:3001
  API_BASE: 'https://maxkb-edu.com/api',

  // 后端不可达时的静态回退
  FALLBACK_ARTICLES:  'articles.json',
  FALLBACK_CHAPTERS:  'assets/js/data.js',   // 内置 chapters 数组
  FALLBACK_AIHOT:     'data/aihot.json',
  FALLBACK_RESOURCES: null,                  // 资源没有静态 fallback，必须登录鉴权

  // 调试开关（生产可改 false）
  DEBUG: false,
};
