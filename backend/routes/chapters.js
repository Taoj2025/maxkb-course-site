import { Router } from 'express';
import { pool } from '../db/pool.js';

const r = Router();

// GET /api/chapters
r.get('/', async (_req, res, next) => {
  try {
    const { rows } = await pool.query(
      `SELECT * FROM chapters WHERE is_active=true ORDER BY sort_order ASC, id ASC`
    );
    res.json({ items: rows });
  } catch (e) { next(e); }
});

export default r;
