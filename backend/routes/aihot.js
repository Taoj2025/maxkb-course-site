import { Router } from 'express';
import { pool } from '../db/pool.js';

const r = Router();

// GET /api/aihot?category=general|fde&limit=30
r.get('/', async (req, res, next) => {
  try {
    const category = req.query.category || 'general';
    const limit = Math.min(100, parseInt(req.query.limit || '30'));
    const { rows } = await pool.query(
      `SELECT id, title, url, summary, source, hot_score, rank, fetched_at
       FROM aihot_items WHERE category=$1
       ORDER BY rank ASC NULLS LAST, hot_score DESC, fetched_at DESC
       LIMIT ${limit}`,
      [category]
    );
    res.json({ items: rows });
  } catch (e) { next(e); }
});

export default r;
