import 'dotenv/config';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pool } from '../db/pool.js';

/**
 * 把静态 AI 热点 JSON 灌进 aihot_items 表
 *
 * 用法：npm run db:import-aihot
 *
 * 数据源（相对 backend/ 的上级目录）：
 *   data/aihot.json      → category='general'（全部热点）
 *   data/aihot-fde.json  → category='fde'（FDE 相关筛选）
 *
 * 幂等：先清掉同 category 的旧数据再写入，重复执行不会产生重复条目。
 * 注意：静态 JSON 里的 category 是中文标签（行业动态 / 技巧观点 / AI 产品…），
 * 表里的 category 是路由用的枚举（general / fde），两者不是一回事，所以不写入该列。
 */

const root = path.resolve(process.cwd(), '..');
const SOURCES = [
  { file: path.join(root, 'data', 'aihot.json'), category: 'general' },
  { file: path.join(root, 'data', 'aihot-fde.json'), category: 'fde' },
];

for (const { file, category } of SOURCES) {
  let json;
  try {
    json = JSON.parse(await fs.readFile(file, 'utf8'));
  } catch (e) {
    console.error(`❌ 无法读取 ${file}: ${e.message}`);
    process.exit(1);
  }

  const items = Array.isArray(json) ? json : (json.items || []);
  if (items.length === 0) {
    console.log(`⚠️  ${path.basename(file)} 没有条目，跳过`);
    continue;
  }

  await pool.query('DELETE FROM aihot_items WHERE category=$1', [category]);

  let inserted = 0;
  for (const [i, it] of items.entries()) {
    const title = (it.title || '').trim();
    if (!title) continue;
    await pool.query(
      `INSERT INTO aihot_items (category, title, url, summary, source, hot_score, rank, fetched_at)
       VALUES ($1,$2,$3,$4,$5,$6,$7, COALESCE($8::timestamptz, NOW()))`,
      [
        category,
        title,
        it.link || it.url || null,
        it.summary || null,
        it.author || json.source || null,
        Number.isFinite(Number(it.hot_score)) ? Number(it.hot_score) : 0,
        i + 1,
        it.pub_date || null,
      ]
    );
    inserted++;
  }
  console.log(`✅ ${category}: 写入 ${inserted} 条（来源 ${path.basename(file)}）`);
}

const { rows } = await pool.query(
  'SELECT category, count(*)::int AS n FROM aihot_items GROUP BY category ORDER BY category'
);
console.log(`📊 汇总: ${rows.map(r => `${r.category}=${r.n}`).join('  ')}`);

process.exit(0);
