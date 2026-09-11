import { Router } from 'express';
import { pool } from '../db/pool.js';

const r = Router();

// GET /api/resources  —— 资源列表（公开）
r.get('/', async (_req, res, next) => {
  try {
    const { rows } = await pool.query(
      `SELECT id, slug, title, description, file_size, min_plan, download_count
       FROM resources WHERE is_active=true ORDER BY created_at ASC`
    );
    res.json({ items: rows });
  } catch (e) { next(e); }
});

export default r;
