/**
 * 把 production 别名指到最新的一次部署
 *
 * 用法：node scripts/assign-vercel-alias.mjs [部署ID]
 *        不带参数 = 自动选最新的、READY 的 production 部署
 *
 * ── 为什么需要这个脚本 ──
 * Vercel 给每个 production 部署挂一个 `deployment-alias` 检查，
 * 用来判断这次部署能不能拿到 production 别名。
 *
 * 2026-10-29 这次部署：构建成功、状态 READY、meta 里 sha 也是对的，
 * 但这个检查一直卡在 pending —— 别名压根没动，
 * 线上 v.taotaoedu.ltd 跑的还是 10-28 那次老部署：
 *
 *   /build-info.json      → 404   （老部署没有静态快照）
 *   /api/health           → 200   （老部署的 api/[...path].js，单段路径）
 *   /api/dl-course/chapters → 404 （多段路径，老部署的 catch-all 只匹配一段）
 *
 * 从页面上完全看不出「部署没生效」—— 首页还是能打开，只有
 * 多段 API 路径在 404。所以每次部署完都要显式把别名指过去，并且
 * 真的去查一遍别名现在指向哪个部署（`vercel inspect` 看不出来）。
 *
 * 别名是可逆的：重新指回去就是回滚。
 */

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const API = 'https://api.vercel.com';

// ── token：优先环境变量，其次读 CLI 的 auth.json ──
function readToken() {
  if (process.env.VERCEL_TOKEN) return process.env.VERCEL_TOKEN;
  const candidates = [
    path.join(ROOT, '.vercel', 'auth.json'),
    path.join(process.env.APPDATA || '', 'com.vercel.cli', 'Data', 'auth.json'),
    path.join(process.env.LOCALAPPDATA || '', 'com.vercel.cli', 'Data', 'auth.json'),
    path.join(os.homedir(), '.local', 'share', 'com.vercel.cli', 'auth.json'),
    path.join(os.homedir(), '.vercel', 'auth.json'),
  ];
  for (const f of candidates) {
    try {
      if (fs.existsSync(f)) {
        const tok = JSON.parse(fs.readFileSync(f, 'utf8')).token;
        if (tok) return tok;
      }
    } catch { /* 忽略，继续找下一个 */ }
  }
  console.error('❌ 找不到 Vercel token。设置环境变量 VERCEL_TOKEN 后重试。');
  process.exit(2);
}

const TOKEN = readToken();

async function api(p, method = 'GET', body) {
  const data = body ? JSON.stringify(body) : undefined;
  const res = await fetch(API + p, {
    method,
    headers: { Authorization: `Bearer ${TOKEN}`, 'Content-Type': 'application/json' },
    body: data,
  });
  const text = await res.text();
  let json;
  try { json = JSON.parse(text); } catch { json = text; }
  if (!res.ok) {
    const err = new Error(typeof json === 'string' ? json.slice(0, 200) : JSON.stringify(json).slice(0, 300));
    err.status = res.status;
    throw err;
  }
  return json;
}

// ── 项目 ──
function projectInfo() {
  const f = path.join(ROOT, '.vercel', 'project.json');
  if (!fs.existsSync(f)) {
    console.error('❌ 没找到 .vercel/project.json —— 先跑 vercel link --project maxkb-course-site-bk10 --yes');
    process.exit(2);
  }
  return JSON.parse(fs.readFileSync(f, 'utf8'));
}

// ── 主流程 ──
const proj = projectInfo();
const projectId = proj.projectId;

console.log('═══════════════════════════════════════════════════');
console.log(`把别名指到最新部署 · ${proj.projectName}`);
console.log('═══════════════════════════════════════════════════');

let deploymentId = process.argv[2] || null;

if (!deploymentId) {
  const list = await api(`/v6/deployments?projectId=${projectId}&target=production&limit=10`);
  const deps = (list.deployments || []).filter((d) => d.readyState === 'READY');
  if (!deps.length) {
    console.error('❌ 没有 READY 状态的 production 部署');
    process.exit(1);
  }
  deps.sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0));
  const dep = deps[0];
  deploymentId = dep.uid;
  console.log(`\n目标部署：${deploymentId}`);
  console.log(`  commit  : ${(dep.meta || {}).githubCommitSha || '(无)'}`);
  console.log(`  作者    : ${(dep.meta || {}).githubCommitAuthorEmail || '(无)'}`);
  console.log(`  创建于  : ${new Date(dep.createdAt).toISOString()}`);
}

// ── 要管的别名：自定义域名 + vercel.app 域名 ──
const domains = await api(`/v9/projects/${projectId}/domains`);
const aliases = (domains.domains || [])
  .map((d) => d.name)
  .filter((n) => !n.endsWith('.taotaoedu.ltd') || n === 'v.taotaoedu.ltd');

// 再加上部署自己的 automaticAliases（团队后缀那种）
const dep = await api(`/v13/deployments/${deploymentId}`);
for (const a of dep.automaticAliases || []) {
  if (!aliases.includes(a)) aliases.push(a);
}

console.log(`\n共 ${aliases.length} 个别名：${aliases.join(', ')}`);

let bad = 0;
console.log('\n【指派】');
for (const alias of aliases) {
  try {
    await api(`/v2/deployments/${deploymentId}/aliases`, 'POST', { alias });
    console.log(`  ✅ ${alias}`);
  } catch (err) {
    console.log(`  ❌ ${alias} —— ${err.message}`);
    bad++;
  }
}

console.log('\n【核对】别名现在到底指向哪个部署');
for (const alias of aliases) {
  try {
    const a = await api(`/v4/aliases/${alias}`);
    const cur = (a.deployment || {}).id;
    const ok = cur === deploymentId;
    if (!ok) bad++;
    console.log(`  ${ok ? '✅' : '❌'} ${alias.padEnd(55)} → ${cur}`);
  } catch (err) {
    bad++;
    console.log(`  ❌ ${alias} —— 查不到：${err.message}`);
  }
}

console.log('\n═══════════════════════════════════════════════════');
if (bad) {
  console.log(`❌ 有 ${bad} 个别名没指到 ${deploymentId}`);
  console.log('═══════════════════════════════════════════════════');
  process.exit(1);
}
console.log(`✅ 全部别名都已指向 ${deploymentId}`);
console.log('   （别名可逆：重新指回旧部署就是回滚）');
console.log('═══════════════════════════════════════════════════');
