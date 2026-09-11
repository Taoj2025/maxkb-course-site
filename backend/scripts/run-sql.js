import 'dotenv/config';
import fs from 'node:fs/promises';
import { pool } from '../db/pool.js';

const file = process.argv[2];
if (!file) {
  console.error('usage: node scripts/run-sql.js <file.sql>');
  process.exit(1);
}

try {
  const sql = await fs.readFile(file, 'utf8');
  await pool.query(sql);
  console.log(`✅ executed ${file}`);
  process.exit(0);
} catch (e) {
  console.error(`❌ failed ${file}:`, e.message);
  process.exit(1);
}
