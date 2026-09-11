import { Router } from 'express';
import bcrypt from 'bcrypt';
import { pool } from '../db/pool.js';
import { signToken, authRequired } from '../middleware/auth.js';

const r = Router();

// POST /api/auth/register
r.post('/register', async (req, res, next) => {
  try {
    const { email, password } = req.body || {};
    if (!email || !password) return res.status(400).json({ error: '邮箱和密码必填' });
    if (password.length < 6)   return res.status(400).json({ error: '密码至少 6 位' });
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return res.status(400).json({ error: '邮箱格式不合法' });

    const hash = await bcrypt.hash(password, 10);
    const { rows } = await pool.query(
      `INSERT INTO users (email, password_hash) VALUES ($1, $2)
       RETURNING id, email, role, plan_id, status, created_at`,
      [email.toLowerCase(), hash]
    );
    const user = rows[0];
    const token = signToken(user);
    res.json({ token, user });
  } catch (e) {
    if (e.code === '23505') return res.status(409).json({ error: '邮箱已注册' });
    next(e);
  }
});

// POST /api/auth/login
r.post('/login', async (req, res, next) => {
  try {
    const { email, password } = req.body || {};
    if (!email || !password) return res.status(400).json({ error: '邮箱和密码必填' });

    const { rows } = await pool.query(
      `SELECT id, email, password_hash, role, plan_id, status FROM users WHERE email=$1`,
      [email.toLowerCase()]
    );
    const user = rows[0];
    if (!user) return res.status(401).json({ error: '邮箱或密码错误' });
    if (user.status === 'banned') return res.status(403).json({ error: '账户已停用，请联系管理员' });

    const ok = await bcrypt.compare(password, user.password_hash);
    if (!ok) return res.status(401).json({ error: '邮箱或密码错误' });

    await pool.query(`UPDATE users SET last_login_at=NOW() WHERE id=$1`, [user.id]);
    delete user.password_hash;
    const token = signToken(user);
    res.json({ token, user });
  } catch (e) { next(e); }
});

// GET /api/auth/me
r.get('/me', authRequired, async (req, res, next) => {
  try {
    const { rows } = await pool.query(
      `SELECT id, email, role, plan_id, status, joined_at, upgraded_at, expires_at,
              total_downloads, last_login_at, created_at FROM users WHERE id=$1`,
      [req.user.sub]
    );
    if (!rows[0]) return res.status(404).json({ error: '用户不存在' });
    res.json({ user: rows[0] });
  } catch (e) { next(e); }
});

export default r;
