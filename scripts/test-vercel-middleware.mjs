/**
 * proxy.mjs（Vercel Routing Middleware）的本地测试
 *
 * 跑法：node scripts/test-vercel-middleware.mjs
 *
 * 打的是真源站，重点验三件事：
 *   1. 多段路径（/api/auth/me、/api/dl-course/chapters…）能进到转发层
 *      —— 这正是 api/[...path].js catch-all 漏掉的那批
 *   2. POST 请求体能原样转发（登录就是 POST）
 *   3. Origin 头被摘掉，源站的 CORS 白名单不会把请求打成 500
 */

const ORIGIN = process.env.ORIGIN_URL || 'https://taotaoedu.ltd';

// 必须在 import 之前设好 —— proxy.mjs 在模块加载时就读了这个变量
process.env.ORIGIN_URL = ORIGIN;

const { default: proxy } = await import('../proxy.mjs');

let pass = 0;
let fail = 0;

function check(name, ok, detail) {
  if (ok) {
    pass++;
    console.log(`  ✅ ${name.padEnd(46)} ${detail ?? ''}`);
  } else {
    fail++;
    console.log(`  ❌ ${name.padEnd(46)} ${detail ?? ''}`);
  }
}

function mkRequest(path, init = {}) {
  const url = new URL(path, 'https://deploy.vercel.app');
  return new Request(url, init);
}

console.log('═══════════════════════════════════════════════════');
console.log(`proxy.mjs 本地测试 · 源站 ${ORIGIN}`);
console.log('═══════════════════════════════════════════════════');

console.log('\n【1】单段路径（原来就能用的）');
{
  const res = await proxy(mkRequest('/api/health'));
  const body = await res.json();
  check('GET /api/health → 200', res.status === 200, `实际 ${res.status}`);
  check('  响应体是源站的 JSON', body && body.ok === true, JSON.stringify(body).slice(0, 60));
}

console.log('\n【2】多段路径（catch-all 漏掉的那批）');
{
  const res = await proxy(mkRequest('/api/auth/me'));
  const body = await res.json();
  check('GET /api/auth/me → 401（未登录）', res.status === 401, `实际 ${res.status}`);
  check('  响应体是源站的 JSON', body && !!body.error, JSON.stringify(body).slice(0, 60));
}
{
  const res = await proxy(mkRequest('/api/dl-course/chapters'));
  const body = await res.json();
  check('GET /api/dl-course/chapters → 200', res.status === 200, `实际 ${res.status}`);
  check('  章节数正确', body && body.total === 9, `total=${body && body.total}`);
}
{
  // 带路径参数的
  const list = await (await proxy(mkRequest('/api/articles'))).json();
  const slug = list && list.items && list.items[0] && list.items[0].slug;
  const res = await proxy(mkRequest(`/api/articles/${encodeURIComponent(slug)}`));
  check(`GET /api/articles/<slug> → 200（slug=${slug}）`, res.status === 200, `实际 ${res.status}`);
}

console.log('\n【3】POST 请求体转发（登录走的就是 POST）');
{
  const res = await proxy(
    mkRequest('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'nobody@example.com', password: 'wrong-password' }),
    })
  );
  const body = await res.json();
  // 源站应该回 401「邮箱或密码错误」—— 说明 body 完整到了后端
  check('POST /api/auth/login（错密码）→ 401', res.status === 401, `实际 ${res.status}`);
  check('  后端确实读到了 body', body && /密码|邮箱/.test(body.error || ''), JSON.stringify(body).slice(0, 70));
}

console.log('\n【4】查询串转发');
{
  const res = await proxy(mkRequest('/api/aihot?category=general'));
  const body = await res.json();
  check('GET /api/aihot?category=general → 200', res.status === 200, `实际 ${res.status}`);
  check('  查询串到达后端（items 只含 general）', body && Array.isArray(body.items), `items=${body && body.items && body.items.length}`);
}

console.log('\n【5】Origin 头必须被摘掉');
{
  // 源站的 cors 白名单里没有 vercel.app，带过去会被打成 500
  const res = await proxy(
    mkRequest('/api/auth/me', { headers: { Origin: 'https://maxkb-course-site-bk10.vercel.app' } })
  );
  check('带 Vercel Origin 的 GET → 401（不是 500）', res.status === 401, `实际 ${res.status}`);
}
{
  const res = await proxy(
    mkRequest('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Origin: 'https://evil.example.com' },
      body: JSON.stringify({ email: 'nobody@example.com', password: 'wrong' }),
    })
  );
  check('带陌生 Origin 的 POST → 401（不是 500）', res.status === 401, `实际 ${res.status}`);
}

console.log('\n【6】预检不能回显任意 Origin');
{
  const res = await proxy(mkRequest('/api/auth/login', { method: 'OPTIONS', headers: { Origin: 'https://evil.example.com' } }));
  check('OPTIONS → 204', res.status === 204, `实际 ${res.status}`);
  const acao = res.headers.get('access-control-allow-origin');
  check('  不回显陌生 Origin', acao === null, `ACAO=${acao}`);
}

console.log('\n【7】响应头完整性');
{
  const res = await proxy(mkRequest('/api/health'));
  check('content-type 透传', !!res.headers.get('content-type'), res.headers.get('content-type'));
  check('content-length 与实际字节数一致', res.headers.get('content-length') === String((await res.clone().arrayBuffer()).byteLength), res.headers.get('content-length'));
  check('content-encoding 不残留', res.headers.get('content-encoding') === null, String(res.headers.get('content-encoding')));
  check('API 不缓存', /no-store/.test(res.headers.get('cache-control') || ''), res.headers.get('cache-control'));
}

console.log('\n【8】源站不可达时要给出 502 而不是崩');
{
  process.env.ORIGIN_URL = 'https://127.0.0.1:9';
  const { default: broken } = await import(`../proxy.mjs?bust=${Date.now()}`);
  const res = await broken(mkRequest('/api/health'));
  check('源站连不上 → 502', res.status === 502, `实际 ${res.status}`);
  process.env.ORIGIN_URL = ORIGIN;
}

console.log('\n═══════════════════════════════════════════════════');
console.log(`通过 ${pass} · 失败 ${fail}`);
console.log('═══════════════════════════════════════════════════');
process.exit(fail === 0 ? 0 : 1);
