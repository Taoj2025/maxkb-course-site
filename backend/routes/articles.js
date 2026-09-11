import { Router } from 'express';
import { pool } from '../db/pool.js';
import { authRequired } from '../middleware/auth.js';
import { adminRequired } from '../middleware/admin.js';

const r = Router();

// GET /api/articles?category=&q=&page=&size=
r.get('/', async (req, res, next) => {
  try {
    const { category, q } = req.query;
    const page  = Math.max(1, parseInt(req.query.page  || '1'));
    const size  = Math.min(50, Math.max(1, parseInt(req.query.size || '20')));
    const offset = (page - 1) * size;

    const where = ['is_published=true'];
    const args  = [];
    if (category) { args.push(category); where.push(`category=$${args.length}`); }
    if (q)        { args.push(`%${q}%`);  where.push(`(title ILIKE $${args.length} OR summary ILIKE $${args.length})`); }
    const wsql = 'WHERE ' + where.join(' AND ');

    const { rows } = await pool.query(
      `SELECT id, slug, title, summary, category, tags, color, author, source,
              estimated_read_time, view_count, published_at
       FROM articles ${wsql}
       ORDER BY published_at DESC
       LIMIT ${size} OFFSET ${offset}`,
      args
    );
    const { rows: cnt } = await pool.query(`SELECT COUNT(*)::int AS n FROM articles ${wsql}`, args);
    res.json({ items: rows, total: cnt[0].n, page, size });
  } catch (e) { next(e); }
});

// GET /api/articles/:slug
r.get('/:slug', async (req, res, next) => {
  try {
    const { rows } = await pool.query(
      `SELECT * FROM articles WHERE slug=$1 AND is_published=true`, [req.params.slug]
    );
    if (!rows[0]) return res.status(404).json({ error: '文章不存在' });
    await pool.query(`UPDATE articles SET view_count = view_count + 1 WHERE id=$1`, [rows[0].id]);
    res.json({ article: rows[0] });
  } catch (e) { next(e); }
});

// POST /api/articles  （管理员）
r.post('/', authRequired, adminRequired, async (req, res, next) => {
  try {
    const { slug, title, summary, category, tags, content_md, color, is_published } = req.body || {};
    if (!slug || !title) return res.status(400).json({ error: 'slug 和 title 必填' });

    const { rows } = await pool.query(
      `INSERT INTO articles (slug, title, summary, category, tags, content_md, color, is_published)
       VALUES ($1,$2,$3,$4,$5,$6,COALESCE($7,'purple'),COALESCE($8,true)) RETURNING *`,
      [slug, title, summary || '', category || '未分类', tags || [], content_md || '', color, is_published]
    );
    res.json({ article: rows[0] });
  } catch (e) {
    if (e.code === '23505') return res.status(409).json({ error: 'slug 已存在' });
    next(e);
  }
});

// PUT /api/articles/:id
r.put('/:id', authRequired, adminRequired, async (req, res, next) => {
  try {
    const { title, summary, category, tags, content_md, color, is_published } = req.body || {};
    const { rows } = await pool.query(
      `UPDATE articles
       SET title=COALESCE($1,title), summary=COALESCE($2,summary),
           category=COALESCE($3,category), tags=COALESCE($4,tags),
           content_md=COALESCE($5,content_md), color=COALESCE($6,color),
           is_published=COALESCE($7,is_published)
       WHERE id=$8 RETURNING *`,
      [title, summary, category, tags, content_md, color, is_published, req.params.id]
    );
    if (!rows[0]) return res.status(404).json({ error: '文章不存在' });
    res.json({ article: rows[0] });
  } catch (e) { next(e); }
});

// DELETE /api/articles/:id
r.delete('/:id', authRequired, adminRequired, async (req, res, next) => {
  try {
    const { rowCount } = await pool.query(`DELETE FROM articles WHERE id=$1`, [req.params.id]);
    if (!rowCount) return res.status(404).json({ error: '文章不存在' });
    res.json({ ok: true });
  } catch (e) { next(e); }
});

export default r;
