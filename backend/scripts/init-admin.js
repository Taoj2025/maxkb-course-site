import 'dotenv/config';
import bcrypt from 'bcrypt';
import { pool } from '../db/pool.js';

const email    = (process.env.ADMIN_EMAIL || '2949465671@qq.com').toLowerCase();
const password = process.env.ADMIN_DEFAULT_PASSWORD || 'tjmtaotao2026';

const hash = await bcrypt.hash(password, 10);

await pool.query(
  `INSERT INTO users (email, password_hash, role, plan_id)
   VALUES ($1, $2, 'admin', 'flagship')
   ON CONFLICT (email) DO UPDATE
     SET password_hash = EXCLUDED.password_hash,
         role          = 'admin',
         plan_id       = 'flagship'`,
  [email, hash]
);

console.log(`✅ admin ${email} 初始化完成`);
console.log(`   默认密码：${password}`);
console.log(`   ⚠️ 请登录后立即在用户中心修改密码！`);

process.exit(0);
