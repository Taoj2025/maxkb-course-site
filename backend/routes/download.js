import { Router } from 'express';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import { pool } from '../db/pool.js';
import { authRequired } from '../middleware/auth.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// 默认指向 backend/ 同级的 ../downloads/（即项目根的 downloads/）
// 也可以用环境变量 DOWNLOADS_DIR 覆盖
const DOWNLOADS_DIR = process.env.DOWNLOADS_DIR
  ? path.resolve(process.env.DOWNLOADS_DIR)
  : path.resolve(__dirname, '../../downloads');

const PLAN_LEVEL = { free: 0, standard: 1, flagship: 2 };
const r = Router();

// GET /api/download/:id   id 可为 UUID 或 slug
r.get('/:id', authRequired, async (req, res, next) => {
  try {
    const uuidRe = /^[0-9a-f-]{36}$/i;
    const sql = uuidRe.test(req.params.id)
      ? `SELECT * FROM resources WHERE id=$1 AND is_active=true`
      : `SELECT * FROM resources WHERE slug=$1 AND is_active=true`;
    const { rows } = await pool.query(sql, [req.params.id]);
    const resource = rows[0];
    if (!resource) return res.status(404).json({ error: '资源不存在' });

    const { rows: urows } = await pool.query(
      `SELECT plan_id, status FROM users WHERE id=$1`, [req.user.sub]
    );
    const user = urows[0];
    if (!user || user.status !== 'active') {
      return res.status(403).json({ error: '账户不可用' });
    }

    const userLevel = PLAN_LEVEL[user.plan_id] ?? 0;
    const needLevel = PLAN_LEVEL[resource.min_plan] ?? 0;
    if (userLevel < needLevel) {
      return res.status(402).json({
        error: '需要升级会员',
        required_plan: resource.min_plan,
        current_plan: user.plan_id,
      });
    }

    const filePath = path.join(DOWNLOADS_DIR, resource.slug);
    if (!fs.existsSync(filePath)) return res.status(404).json({ error: '文件不存在，请联系管理员' });

    // 记录下载 + 更新计数
    await pool.query(
      `INSERT INTO downloads (user_id, resource_id, ip_address, user_agent, referer)
       VALUES ($1,$2,$3,$4,$5)`,
      [req.user.sub, resource.id, req.ip,
       (req.headers['user-agent'] || '').slice(0, 500),
       (req.headers['referer']   || '').slice(0, 500)]
    );
    await pool.query(`UPDATE resources SET download_count = download_count + 1 WHERE id=$1`, [resource.id]);
    await pool.query(`UPDATE users    SET total_downloads = total_downloads + 1 WHERE id=$1`, [req.user.sub]);

    // 流式转发（不暴露静态 URL）
    //
    // Content-Length 必须用磁盘上的真实大小，不能用 resources.file_size：
    // 那列是 seed 里写死的常量，文件改动后（比如替换了讲义）就对不上了，
    // 头里写 19385、实际只发 18814 字节，浏览器收到的是一个被截断的包，
    // 用户看到的是「下载失败」。真实大小永远以文件为准。
    const stat = fs.statSync(filePath);
    const ext = path.extname(resource.slug);
    // 文件名用资源标题（如「MaxKB FDE 教学课件.pptx」），而不是 r_a1b2c3d4 这种
    // 占位 slug —— 用户下载到本地后能一眼看出是什么文件。
    const base = resource.title || path.basename(resource.slug, ext);
    const filename = `${base}${ext}`;
    // filename 存 ASCII 兜底，filename* 存 UTF-8 原名（RFC 6266）
    const asciiName = filename.replace(/[^\x20-\x7E]/g, '_').replace(/["\\]/g, '_');

    res.setHeader('Content-Type', 'application/octet-stream');
    res.setHeader(
      'Content-Disposition',
      `attachment; filename="${asciiName}"; filename*=UTF-8''${encodeURIComponent(filename)}`
    );
    res.setHeader('Content-Length', stat.size);
    fs.createReadStream(filePath).pipe(res);
  } catch (e) { next(e); }
});

export default r;
