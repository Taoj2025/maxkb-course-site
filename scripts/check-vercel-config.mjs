/**
 * Vercel 部署配置自检 —— 提交前 / 部署前跑一遍
 *
 * 用法：node scripts/check-vercel-config.mjs
 *
 * 专门盯两类「构建时才炸、线上却看不出来」的坑：
 *
 *   1) matcher 配两处 → Vercel 构建直接失败 → 部署不生效，
 *      线上还是旧版本（症状：改了半天没反应）。
 *   2) api/ 目录里的 [...xxx].js 不是 catch-all —— Vercel 生成路由时
 *      把文件名里的 [...] 当成单段动态参数，只匹配一段路径。
 *      多段路径（/api/auth/login）会落到 Vercel 自己的 404 页。
 *
 * 检查完还会拿前端真正调用的 /api 路径逐条过中间件的正则，
 * 确保没有漏网的路径会绕开转发层。
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

let pass = 0;
let fail = 0;
const warn = [];

function check(name, ok, detail = '') {
  if (ok) {
    pass++;
    console.log(`  ✅ ${name.padEnd(50)} ${detail}`);
  } else {
    fail++;
    console.log(`  ❌ ${name.padEnd(50)} ${detail}`);
  }
}

function note(name, detail) {
  warn.push(name);
  console.log(`  ⚠️  ${name.padEnd(50)} ${detail}`);
}

console.log('═══════════════════════════════════════════════════');
console.log('Vercel 配置自检');
console.log('═══════════════════════════════════════════════════');

// ── 读 vercel.json ──
let vercel;
try {
  vercel = JSON.parse(fs.readFileSync(path.join(ROOT, 'vercel.json'), 'utf8'));
} catch (err) {
  console.error(`❌ vercel.json 解析失败：${err.message}`);
  process.exit(1);
}

console.log('\n【1】proxy 配置');
const proxy = vercel.proxy || {};
check('vercel.json 有 proxy.entrypoint', typeof proxy.entrypoint === 'string' && proxy.entrypoint.length > 0, proxy.entrypoint || '(缺失)');

const entryPath = path.join(ROOT, proxy.entrypoint || '');
check('proxy.entrypoint 文件存在', fs.existsSync(entryPath), proxy.entrypoint);
const entrySrc = fs.existsSync(entryPath) ? fs.readFileSync(entryPath, 'utf8') : '';

// ← 本次事故的元凶：matcher 只能配一处
const fileHasMatcher = /export\s+const\s+config\s*=\s*\{[^}]*\bmatcher\b/s.test(entrySrc);
const jsonHasMatcher = typeof proxy.matcher === 'string' && proxy.matcher.length > 0;
check('matcher 只配了一处（不能两边都配）', !(fileHasMatcher && jsonHasMatcher),
  fileHasMatcher && jsonHasMatcher
    ? '❌ 两边都配了 → Vercel 构建会失败，部署不生效'
    : `vercel.json=${jsonHasMatcher ? '有' : '无'} / ${proxy.entrypoint}=${fileHasMatcher ? '有' : '无'}`);

if (fileHasMatcher && jsonHasMatcher) {
  console.log('     └─ Vercel 报错原文：proxy.matcher in vercel.json conflicts with config.matcher');
  console.log('        exported from the proxy entrypoint. Configure the matcher in only one location.');
}

// ── 中间件覆盖范围 ──
console.log('\n【2】中间件拦截范围');
let matcherRe = null;
if (jsonHasMatcher) {
  // path-to-regexp v6 语法：:name* = 零段或多段
  const toRegex = (m) => {
    const escaped = m.replace(/[.+^${}()|[\]\\]/g, '\\$&').replace(/\/:(\w+)\*/g, '(?:/(.*))?');
    return new RegExp('^' + escaped + '$');
  };
  matcherRe = toRegex(proxy.matcher);
  check('proxy.matcher 是合法字符串', true, proxy.matcher);
} else {
  note('vercel.json 没写 proxy.matcher', '转发层会拦下所有路径（等于全站转发），确认这是有意的');
}

// ── api/ 目录的 catch-all 陷阱 ──
console.log('\n【3】api/ 目录的 catch-all 陷阱');
const apiDir = path.join(ROOT, 'api');
if (fs.existsSync(apiDir)) {
  const apiFiles = [];
  (function walk(dir, base = '') {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const rel = base ? `${base}/${e.name}` : e.name;
      if (e.isDirectory()) walk(path.join(dir, e.name), rel);
      else apiFiles.push(rel);
    }
  })(apiDir);

  for (const f of apiFiles) {
    // Vercel 的 createRouteFromPath：文件名里 [...x] → ([^/]+)，只匹配一段
    const isCatchAll = /\[.*\.\.\..*\]/.test(f);
    if (isCatchAll) {
      note(`${f} 不是真 catch-all`, 'Vercel 会把它当单段参数 → ^/api/([^/]+)$，多段路径会 404');
    }
  }
  if (!apiFiles.some((f) => /\[.*\.\.\..*\]/.test(f))) {
    check('api/ 目录没有误导性的 catch-all 文件名', true, apiFiles.join(', ') || '(空)');
  }
}

// ── 前端真正调用的路径 ──
console.log('\n【4】前端调用的 /api 路径是否都被转发层覆盖');
const apiPaths = new Set();
const scanDirs = ['assets/js'];
for (const dir of scanDirs) {
  const abs = path.join(ROOT, dir);
  if (!fs.existsSync(abs)) continue;
  for (const f of fs.readdirSync(abs)) {
    if (!f.endsWith('.js')) continue;
    const src = fs.readFileSync(path.join(abs, f), 'utf8');
    for (const m of src.matchAll(/['"`](\/api\/[^'"`\s]*)/g)) apiPaths.add(m[1]);
  }
}
for (const f of fs.readdirSync(ROOT)) {
  if (!f.endsWith('.html')) continue;
  const src = fs.readFileSync(path.join(ROOT, f), 'utf8');
  for (const m of src.matchAll(/['"`](\/api\/[^'"`\s]*)/g)) apiPaths.add(m[1]);
}

if (apiPaths.size === 0) {
  note('没扫到前端调用的 /api 路径', '静态扫描能力有限，跳过');
} else {
  const sample = (p) => p.replace(/\$\{[^}]*\}/g, 'sample-id').replace(/\?.*$/, '');
  const uncovered = [];
  for (const p of [...apiPaths].sort()) {
    const concrete = sample(p);
    const ok = matcherRe ? matcherRe.test(concrete) : true;
    if (!ok) uncovered.push(concrete);
  }
  check('前端用到的所有 /api 路径都在 matcher 内', uncovered.length === 0,
    uncovered.length ? `漏了：${uncovered.join(', ')}` : `${apiPaths.size} 条路径全覆盖`);
}

console.log('\n═══════════════════════════════════════════════════');
console.log(`通过 ${pass} · 失败 ${fail}${warn.length ? ` · 警告 ${warn.length}` : ''}`);
console.log('═══════════════════════════════════════════════════');
process.exit(fail === 0 ? 0 : 1);
