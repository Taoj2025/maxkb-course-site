/**
 * 代理函数本地自测 —— 不依赖 Vercel，直接打源站。
 * 用法：node scripts/test-vercel-proxy.cjs
 */
const handler = require('../api/[...path].js');
const { Readable } = require('stream');

function mockRes() {
  const r = {
    _status: 200,
    _headers: {},
    _body: null,
    status(c) { r._status = c; return r; },
    setHeader(k, v) { r._headers[k.toLowerCase()] = v; return r; },
    json(o) { r._body = o; r._headers['content-type'] = 'application/json'; return r; },
    send(b) { r._body = b; return r; },
    end() { return r; },
  };
  return r;
}

async function call({ method = 'GET', url = '/api/health', headers = {}, body = null }) {
  const req = Readable.from(body ? [Buffer.from(body)] : []);
  req.method = method;
  req.url = url;
  req.headers = { host: 'taotaoedu.ltd', ...headers };
  const res = mockRes();
  await handler(req, res);
  return res;
}

(async () => {
  const cases = [
    { name: 'GET /api/health', opts: { url: '/api/health' } },
    { name: 'GET /api/articles', opts: { url: '/api/articles' } },
    { name: 'GET /api/articles?category=general', opts: { url: '/api/articles?category=general' } },
    { name: 'GET /api/dl-course/chapters', opts: { url: '/api/dl-course/chapters' } },
    { name: 'POST /api/auth/login（错密码，应 401 不是 404）',
      opts: { method: 'POST', url: '/api/auth/login', headers: { 'content-type': 'application/json' },
               body: JSON.stringify({ email: 'nobody@example.com', password: 'x' }) } },
    { name: 'GET /api/auth/me（无 token，应 401）', opts: { url: '/api/auth/me' } },
    { name: '带 Origin 头的 POST（Vercel 域名不在源站 CORS 白名单，应正常而不是 500）',
      opts: { method: 'POST', url: '/api/auth/login',
               headers: { 'content-type': 'application/json', origin: 'https://my-app.vercel.app' },
               body: JSON.stringify({ email: 'nobody@example.com', password: 'x' }) } },
    { name: 'GET /api/download/r_m3n4o5p6.md（付费墙）', opts: { url: '/api/download/r_m3n4o5p6.md' } },
    { name: 'GET /api/nonexistent（应 404）', opts: { url: '/api/nonexistent' } },
  ];

  for (const c of cases) {
    try {
      const res = await call(c.opts);
      const body = res._body;
      const preview = Buffer.isBuffer(body)
        ? body.toString('utf8').slice(0, 70).replace(/\s+/g, ' ')
        : JSON.stringify(body).slice(0, 70);
      console.log(`  ${String(res._status).padEnd(4)} ${c.name}`);
      console.log(`       ${preview}`);
    } catch (e) {
      console.log(`  ERR  ${c.name}\n       ${e.message}`);
    }
  }
})();
