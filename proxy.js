/**
 * Vercel Routing Middleware —— 把 /api/* 转发到源站
 *
 * 为什么要这层：
 *   后端跑在自建服务器上（systemd + 本地 PostgreSQL）。
 *   如果让 Vercel 直连数据库，就得把生产库的 5432 端口开放到公网，
 *   等于把 postgres 超级用户密码交给云平台 —— 这个代价太大。
 *
 *   所以 Vercel 只做「CDN + 转发层」：请求进来，转发给源站，响应原路返回。
 *   好处是 vercel.json 的 env 可以是空的 ——
 *   不需要任何数据库 / OSS / 微信凭证，也不需要在云平台存任何密钥。
 *
 * 为什么用 Routing Middleware 而不是 api/[...path].js：
 *   Vercel 生成 api 目录路由时（createRouteFromPath），文件名里的
 *   [xxx] 一律当成「单段动态参数」—— 哪怕写的是 [...path]。
 *   实测：api/[...path].js 生成的正则是 ^/api/([^/]+)$ ，
 *   只匹配一段。/api/health、/api/articles 走函数，而 /api/auth/login、
 *   /api/auth/me、/api/download/<slug>、/api/dl-course/chapters 这些
 *   多段路径全部落到 Vercel 自己的 404 页，函数根本没被调用。
 *   而登录、会员校验、付费下载全是多段路径 —— 等于核心链路全断。
 *
 *   Routing Middleware 在路由之前执行，matcher 用官方文档给的
 *   /api/:func*（:func* = 零段或多段），任意深度的路径都能进到这里，
 *   而且拿到的是原始请求路径，不用猜。
 *
 * 运行时：Node.js runtime。
 *
 * ⚠️ 文件名必须是 proxy.js，不能是 proxy.mjs：
 *    Vercel 只接受 .js / .ts（或 Python 的 module:attr）作为 proxy 入口，
 *    写成 .mjs 会在部署时被直接拒掉：
 *      The `proxy.entrypoint` must be a `.js` or `.ts` file path,
 *      or a Python `module:attr`.
 *    线上表现是「部署不生效」—— 旧版本继续跑，多段 API 路径照旧 404。
 *    （2026-10-29 就是这么白查了一轮。）
 *
 *    本文件用 ESM 语法（export const config / export default），
 *    仓库根 package.json 没有 "type": "module"，
 *    但 Vercel 构建中间件时用 esbuild 打包，ESM 语法照样认。
 *    api/[...path].js 保持 CommonJS。
 */

const ORIGIN = (process.env.ORIGIN_URL || 'https://taotaoedu.ltd').replace(/\/+$/, '');

// 允许跨域访问的来源。只有在预检时才会用到 ——
// 浏览器访问 Vercel 是同源的，正常根本不会发预检。
const ALLOWED_ORIGINS = (process.env.CORS_ORIGINS || '')
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean);

// 这些响应头不能原样回传：
//   connection/keep-alive/... 是逐跳首部，不能穿过代理
//   content-encoding —— fetch 会自动解压响应体，照抄会让客户端以为还是 gzip
//   content-length —— 解压后长度变了，照抄会把响应体截断
const SKIP_RESPONSE_HEADERS = new Set([
  'connection',
  'keep-alive',
  'transfer-encoding',
  'upgrade',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailer',
  'content-encoding',
  'content-length',
  'server',
  'x-powered-by',
]);

// ⚠️ 这里绝对不要再写 matcher！
//    matcher 只能在一处配置：要么 vercel.json 的 proxy.matcher，
//    要么本文件导出的 config.matcher —— 两处都写，Vercel 构建会直接失败：
//      "proxy.matcher in vercel.json conflicts with config.matcher
//       exported from the proxy entrypoint. Configure the matcher in
//       only one location."
//    构建失败 = 部署不生效，线上还是旧版本（2026-10-29 就踩过这个坑，
//    症状是多段 API 路径继续 404）。
//    本仓库把 matcher 放在 vercel.json 里（和 entrypoint 挨着，方便看）。
export const config = {
  runtime: 'nodejs',
};

export default async function proxy(request) {
  const incoming = new URL(request.url);

  // ── 预检 ──
  // 不回显任意 Origin：只认白名单里的。
  // 否则任何站点都能拿自己的 origin 预检通过，再对 Vercel 这个域发请求。
  if (request.method === 'OPTIONS') {
    const headers = new Headers({
      'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type,Authorization',
      Vary: 'Origin',
    });
    const origin = request.headers.get('origin');
    if (origin && ALLOWED_ORIGINS.includes(origin)) {
      headers.set('Access-Control-Allow-Origin', origin);
    }
    return new Response(null, { status: 204, headers });
  }

  // request.url 是完整路径（含 query），例如 /api/articles?category=general
  const target = `${ORIGIN}${incoming.pathname}${incoming.search}`;

  // ── 转发请求头 ──
  const headers = new Headers();
  for (const [key, value] of request.headers.entries()) {
    const k = key.toLowerCase();
    // host 由 fetch 自己填（要跟目标域名一致），content-length 由 fetch 按 body 算
    if (k === 'host' || k === 'content-length') continue;
    // accept-encoding 让 fetch 自己处理，否则解压后长度对不上
    if (k === 'accept-encoding') continue;
    // origin 必须摘掉：源站的 cors 中间件只放行白名单里的 origin，
    // Vercel 的域名不在白名单里，带过去会被拒（500）。
    // 浏览器这边是同源请求，源站看不到 origin 就会直接放行。
    if (k === 'origin') continue;
    headers.set(key, value);
  }

  // ── 读请求体 ──
  let body;
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    const buf = await request.arrayBuffer();
    body = buf.byteLength ? buf : undefined;
  }

  // ── 转发到源站 ──
  let upstream;
  try {
    upstream = await fetch(target, {
      method: request.method,
      headers,
      body,
      redirect: 'manual',
    });
  } catch (err) {
    return new Response(
      JSON.stringify({ error: `源站不可达：${err.message}`, target }),
      {
        status: 502,
        headers: { 'Content-Type': 'application/json; charset=utf-8' },
      }
    );
  }

  // ── 回传响应 ──
  const out = new Headers();
  for (const [key, value] of upstream.headers.entries()) {
    if (SKIP_RESPONSE_HEADERS.has(key.toLowerCase())) continue;
    out.set(key, value);
  }
  // set-cookie 可能有多个，entries() 会把它们并成一个字符串，得单独取
  const cookies =
    typeof upstream.headers.getSetCookie === 'function'
      ? upstream.headers.getSetCookie()
      : [];
  for (const cookie of cookies) out.append('set-cookie', cookie);

  // API 一律不缓存
  out.set('cache-control', 'no-store, no-cache, must-revalidate');

  // 缓冲后回传：这样 content-length 一定和实际字节数对得上
  // （源站可能开了 gzip，fetch 解压后长度会变）
  const payload = await upstream.arrayBuffer();
  out.set('content-length', String(payload.byteLength));

  // 204 / 304 这类状态码不允许带响应体
  const nullBody = [101, 204, 205, 304].includes(upstream.status);

  return new Response(nullBody ? null : payload, {
    status: upstream.status,
    headers: out,
  });
}
