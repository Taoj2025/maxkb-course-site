import pg from 'pg';
import 'dotenv/config';

const { Pool } = pg;

export const pool = new Pool({
  host:     process.env.PGHOST,
  port:     Number(process.env.PGPORT) || 5432,
  user:     process.env.PGUSER,
  password: process.env.PGPASSWORD,
  database: process.env.PGDATABASE,
  max: 10,
  idleTimeoutMillis: 30_000,
  ssl: process.env.PGSSL === 'true' ? { rejectUnauthorized: false } : false,
});

// 启动时测试一次连接
pool.query('SELECT NOW()').then(r => {
  if (process.env.NODE_ENV !== 'production') {
    console.log(`[db] connected at ${r.rows[0].now}`);
  }
}).catch(e => {
  console.error('[db] connection failed:', e.message);
});
