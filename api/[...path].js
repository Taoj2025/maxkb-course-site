/**
 * Vercel 边缘代理 —— 把 /api/* 转发到源站
 *
 * 为什么要这么绕：
 *   后端跑在自建服务器上（systemd + 本地 PostgreSQL）。
 *   如果让 Vercel 的函数直连数据库，就得把生产库的 5432 端口开放到公网，
 *   等于把 postgres 超级用户密码交给云函数 —— 这个代价太大。
 *
 *   所以 Vercel 只做「CDN + 转发层」：请求进来，转发给源站，响应原路返回。
 *   好处是 vercel.json 的 env 可以是空的 ——
 *   不需要任何数据库 / OSS / 微信凭证，也不需要在云平台存任何密钥。
 *
 * 路由：api/[...path].js 是 catch-all，一个文件覆盖源站全部 /api/* 路由
 *       （auth / articles / chapters / contact / aihot / resources /
 *        download / dl-course / admin）。
 *
 * 运行时：Vercel Node.js runtime。仓库根目录没有 package.json，
 *         所以 .js 按 CommonJS 处理。
 */

// 源站地址。Vercel 环境变量里可以覆盖（多环境部署时有用）。
const ORIGIN = (process.env.ORIGIN_URL || 'https://taotaoedu.ltd').replace(/\/+$/, '');

module.exports = async function handler(req, res) {
  // req.url 是完整路径（含 query），例如 /api/articles?category=general
  const incoming = new URL(req.url, 'http://internal');
  // /api/articles -> /articles，再拼回源站的 /api 前缀
  const rest = incoming.pathname.replace(/^\/api/, '') || '/';
  const target = `${ORIGIN}/api${rest}${incoming.search}`;

  // ── 预检 ──
  // 浏览器访问 Vercel 是同源的，正常不会发预检；
  // 万一有人跨域直连这个函数，这里给个放行。
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', req.headers.origin || '*');
    res.setHeader('Access-Control-Allow-Credentials', 'true');
    res.setHeader('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type,Authorization');
    return res.status(204).end();
  }

  // ── 转发请求头 ──
  const headers = {};
  for (const [k, v] of Object.entries(req.headers || {})) {
    const key = k.toLowerCase();
    // host 由 fetch 自己填（要跟目标域名一致），content-length 由 fetch 按 body 算
    if (key === 'host' || key === 'content-length') continue;
    // origin 必须摘掉：源站的 cors 中间件只放行白名单里的 origin，
    // Vercel 的域名不在白名单里，带过去会被拒（500）。
    // 浏览器这边是同源请求，源站看不到 origin 就会直接放行。
    if (key === 'origin') continue;
    headers[k] = v;
  }

  // ── 读请求体 ──
  let body;
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    body = Buffer.concat(chunks);
    if (body.length === 0) body = undefined;
  }

  // ── 转发到源站 ──
  let upstream;
  try {
    upstream = await fetch(target, {
      method: req.method,
      headers,
      body,
      redirect: 'manual',
    });
  } catch (err) {
    return res.status(502).json({
      error: `源站不可达：${err.message}`,
      target,
    });
  }

  // ── 回传响应 ──
  // 下载接口要透传 content-disposition（文件名在里面），
  // 还要透传 content-length（源站给的字节数是准的）。
  const passthrough = [
    'content-type',
    'content-disposition',
    'content-length',
    'cache-control',
    'etag',
    'last-modified',
  ];
  for (const name of passthrough) {
    const v = upstream.headers.get(name);
    if (v) res.setHeader(name, v);
  }
  const cookies = (upstream.headers.getSetCookie && upstream.headers.getSetCookie()) || [];
  if (cookies.length) res.setHeader('set-cookie', cookies);
  const location = upstream.headers.get('location');
  if (location) res.setHeader('location', location);

  const buf = Buffer.from(await upstream.arrayBuffer());
  res.status(upstream.status);
  return res.send(buf);
};
