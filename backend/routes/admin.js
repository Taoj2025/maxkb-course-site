import { Router } from 'express';
import { pool } from '../db/pool.js';
import { authRequired } from '../middleware/auth.js';
import { adminRequired } from '../middleware/admin.js';

const r = Router();
r.use(authRequired, adminRequired);

async function logAction(req, action, targetType, targetId, details) {
  await pool.query(
    `INSERT INTO admin_logs (admin_email, action, target_type, target_id, details, ip_address)
     VALUES ($1,$2,$3,$4,$5,$6)`,
    [req.user.email, action, targetType || null, targetId || null,
     details || null, req.ip]
  );
}

// GET /api/admin/users?page=&size=&q=
r.get('/users', async (req, res, next) => {
  try {
    const page  = Math.max(1, parseInt(req.query.page || '1'));
    const size  = Math.min(100, Math.max(1, parseInt(req.query.size || '20')));
    const offset = (page - 1) * size;
    const q = req.query.q;
    const args = [];
    let where = '';
    if (q) { args.push(`%${q}%`); where = 'WHERE email ILIKE $1'; }
    const { rows } = await pool.query(
      `SELECT id, email, role, plan_id, status, joined_at, upgraded_at, expires_at,
              total_downloads, last_login_at, created_at FROM users ${where}
       ORDER BY created_at DESC LIMIT ${size} OFFSET ${offset}`, args);
    const { rows: cnt } = await pool.query(`SELECT COUNT(*)::int AS n FROM users ${where}`, args);
    res.json({ items: rows, total: cnt[0].n, page, size });
  } catch (e) { next(e); }
});

// POST /api/admin/users/:id/upgrade  body: { plan }
r.post('/users/:id/upgrade', async (req, res, next) => {
  try {
    const { plan } = req.body || {};
    if (!['free', 'standard', 'flagship'].includes(plan)) {
      return res.status(400).json({ error: 'plan 必须是 free/standard/flagship' });
    }
    const expires = plan === 'free' ? null
      : new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString();
    const { rows } = await pool.query(
      `UPDATE users SET plan_id=$1, upgraded_at=NOW(), expires_at=$2 WHERE id=$3 RETURNING *`,
      [plan, expires, req.params.id]);
    if (!rows[0]) return res.status(404).json({ error: '用户不存在' });
    await logAction(req, 'upgrade_user', 'user', req.params.id, { plan });
    res.json({ user: rows[0] });
  } catch (e) { next(e); }
});

// POST /api/admin/users/:id/downgrade  （强制降到 free）
r.post('/users/:id/downgrade', async (req, res, next) => {
  try {
    const { rows } = await pool.query(
      `UPDATE users SET plan_id='free', upgraded_at=NOW(), expires_at=NULL WHERE id=$1 RETURNING *`,
      [req.params.id]);
    if (!rows[0]) return res.status(404).json({ error: '用户不存在' });
    await logAction(req, 'downgrade_user', 'user', req.params.id);
    res.json({ user: rows[0] });
  } catch (e) { next(e); }
});

// POST /api/admin/users/:id/ban
r.post('/users/:id/ban', async (req, res, next) => {
  try {
    const { rows } = await pool.query(
      `UPDATE users SET status='banned' WHERE id=$1 RETURNING id, email, status`,
      [req.params.id]);
    if (!rows[0]) return res.status(404).json({ error: '用户不存在' });
    await logAction(req, 'ban_user', 'user', req.params.id);
    res.json({ user: rows[0] });
  } catch (e) { next(e); }
});

// POST /api/admin/users/:id/unban
r.post('/users/:id/unban', async (req, res, next) => {
  try {
    const { rows } = await pool.query(
      `UPDATE users SET status='active' WHERE id=$1 RETURNING id, email, status`,
      [req.params.id]);
    if (!rows[0]) return res.status(404).json({ error: '用户不存在' });
    await logAction(req, 'unban_user', 'user', req.params.id);
    res.json({ user: rows[0] });
  } catch (e) { next(e); }
});

// GET /api/admin/stats
r.get('/stats', async (_req, res, next) => {
  try {
    const [totals, byPlan, downloads, recent, newArticles] = await Promise.all([
      pool.query(`SELECT COUNT(*)::int AS n FROM users`),
      pool.query(`SELECT plan_id, COUNT(*)::int AS n FROM users GROUP BY plan_id`),
      pool.query(`SELECT COUNT(*)::int AS n FROM downloads`),
      pool.query(`SELECT COUNT(*)::int AS n FROM contact_messages WHERE status='new'`),
      pool.query(`SELECT COUNT(*)::int AS n FROM articles WHERE is_published=true`),
    ]);
    const planMap = Object.fromEntries(byPlan.rows.map(r => [r.plan_id, r.n]));
    const revenue = (planMap.standard || 0) * 99 + (planMap.flagship || 0) * 299;
    res.json({
      total_users:            totals.rows[0].n,
      plan_distribution:      planMap,
      total_downloads:        downloads.rows[0].n,
      new_messages:           recent.rows[0].n,
      published_articles:     newArticles.rows[0].n,
      estimated_revenue_yuan: revenue,
    });
  } catch (e) { next(e); }
});

// GET /api/admin/logs?limit=50
r.get('/logs', async (req, res, next) => {
  try {
    const limit = Math.min(200, parseInt(req.query.limit || '50'));
    const { rows } = await pool.query(
      `SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT $1`, [limit]);
    res.json({ items: rows });
  } catch (e) { next(e); }
});

export default r;
