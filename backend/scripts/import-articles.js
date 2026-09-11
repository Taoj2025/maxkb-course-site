import 'dotenv/config';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pool } from '../db/pool.js';

// backend/ → 项目根目录的 articles/
const root = path.resolve(process.cwd(), '..');
const dir  = path.join(root, 'articles');

let files;
try {
  files = await fs.readdir(dir);
} catch (e) {
  console.error(`❌ 无法读取 ${dir}:`, e.message);
  process.exit(1);
}

let updated = 0, skipped = 0, failed = 0;
for (const f of files) {
  if (!f.endsWith('.md')) continue;
  const slug = f.replace(/\.md$/, '');
  try {
    const md = await fs.readFile(path.join(dir, f), 'utf8');
    const r = await pool.query(
      `UPDATE articles SET content_md=$1, updated_at=NOW() WHERE slug=$2`,
      [md, slug]
    );
    if (r.rowCount > 0) {
      console.log(`  ✓ ${slug}`);
      updated++;
    } else {
      console.log(`  ⚠ skipped (slug 不在 DB): ${slug}`);
      skipped++;
    }
  } catch (e) {
    console.error(`  ✗ ${slug}:`, e.message);
    failed++;
  }
}

console.log(`\n📊 summary: updated=${updated}, skipped=${skipped}, failed=${failed}`);
process.exit(0);
