import { Router } from 'express';
import { pool } from '../db/pool.js';

const r = Router();

// POST /api/contact
// body: { name, email, phone, company, subject, message, source }
r.post('/', async (req, res, next) => {
  try {
    const { name, email, phone, company, subject, message, source } = req.body || {};
    if (!message || !message.trim()) return res.status(400).json({ error: '留言内容必填' });

    const { rows } = await pool.query(
      `INSERT INTO contact_messages
        (name, email, phone, company, subject, message, source, ip_address, user_agent)
       VALUES ($1,$2,$3,$4,$5,$6,COALESCE($7,'index'),$8,$9)
       RETURNING id, created_at`,
      [
        name || null,
        email || null,
        phone || null,
        company || null,
        subject || null,
        message,
        source,
        req.ip,
        (req.headers['user-agent'] || '').slice(0, 500),
      ]
    );
    res.json({ ok: true, id: rows[0].id, created_at: rows[0].created_at });
  } catch (e) { next(e); }
});

export default r;
