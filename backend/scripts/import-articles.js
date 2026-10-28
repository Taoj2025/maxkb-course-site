/**
 * 把 articles.json + articles/*.md 同步进数据库的 articles 表
 *
 *   npm run db:import-articles
 *
 * 为什么以 articles.json 为准：
 *   articles.json 才是内容流水线真正维护的那份清单（auto_review_and_publish.py
 *   每天往里追加新文章），latest.html / article.html 读的都是它。
 *   以前这个脚本只做 UPDATE（且用文件名当 slug 去匹配），数据库里留着
 *   一批 slug 是「文件名」、内容却和 articles.json 重号的种子数据，
 *   于是 /api/articles 返回的是另一套文章，首页资讯点进去全是
 *   「❌ 未找到该文章」。
 *
 * 现在改成全量对齐：id / slug / 标题 / 正文 / 时间全部以 articles.json 为准，
 * 数据库里不在清单里的行直接删掉，保证 API 和静态清单永远是同一份。
 *
 * 幂等：重复执行结果一致。
 */
import 'dotenv/config';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pool } from '../db/pool.js';

// backend/ → 项目根目录（/opt/maxkb-api，里面是指回仓库的软链）
const root = path.resolve(process.cwd(), '..');
const ARTICLES_DIR = path.join(root, 'articles');
const LIST_FILE = path.join(root, 'articles.json');

/**
 * 定位文章正文文件。历史上存在过三种命名：
 *   <id>-<slug>.md   多数文章
 *   <slug>.md        老数据
 *   <id>.md          兜底
 * article.json 里新增的 file 字段最准，没有就按上面的顺序试。
 */
async function resolveFile(entry) {
  const { id, slug } = entry;
  const candidates = [
    entry.file,
    id && slug ? `${id}-${slug}.md` : null,
    slug ? `${slug}.md` : null,
    id ? `${id}.md` : null,
  ].filter(Boolean);

  for (const name of candidates) {
    try {
      await fs.access(path.join(ARTICLES_DIR, name));
      return name;
    } catch { /* 试下一个 */ }
  }
  return null;
}

function toTags(tags) {
  if (Array.isArray(tags)) return tags.filter(Boolean);
  if (typeof tags === 'string') return tags.split(',').map((s) => s.trim()).filter(Boolean);
  return [];
}

async function main() {
  let list;
  try {
    list = JSON.parse(await fs.readFile(LIST_FILE, 'utf8'));
  } catch (e) {
    console.error(`❌ 读不到文章清单 ${LIST_FILE}:`, e.message);
    process.exit(1);
  }

  const items = Array.isArray(list) ? list : (list.articles || list.items || []);
  if (!items.length) {
    console.error('❌ 文章清单是空的，不做任何改动');
    process.exit(1);
  }

  console.log(`📄 清单 ${items.length} 篇，开始同步…`);

  let inserted = 0, updated = 0, missingFile = 0;
  const ids = [];

  for (const entry of items) {
    const id = Number(entry.id);
    const slug = entry.slug || String(entry.id);
    if (!Number.isFinite(id)) {
      console.error(`  ⚠ 跳过：id 非法 (${entry.id})`);
      continue;
    }
    ids.push(id);

    const file = await resolveFile(entry);
    let content = '';
    if (file) {
      content = await fs.readFile(path.join(ARTICLES_DIR, file), 'utf8');
    } else {
      missingFile++;
      console.error(`  ⚠ ${id} 找不到正文文件（${slug}）`);
    }

    // 日期只到天，按东八区零点解析，避免落到前一天
    const publishedAt = entry.date
      ? new Date(`${entry.date}T00:00:00+08:00`)
      : new Date();

    const r = await pool.query(
      `INSERT INTO articles
         (id, slug, title, summary, category, tags, color, content_md,
          author, source, estimated_read_time, is_published, published_at)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,TRUE,$12)
       ON CONFLICT (id) DO UPDATE SET
         slug            = EXCLUDED.slug,
         title           = EXCLUDED.title,
         summary         = EXCLUDED.summary,
         category        = EXCLUDED.category,
         tags            = EXCLUDED.tags,
         color           = EXCLUDED.color,
         content_md      = EXCLUDED.content_md,
         author          = EXCLUDED.author,
         source          = EXCLUDED.source,
         estimated_read_time = EXCLUDED.estimated_read_time,
         published_at    = EXCLUDED.published_at,
         updated_at      = NOW()
       RETURNING (xmax = 0) AS inserted`,
      [
        id,
        slug,
        entry.title || slug,
        entry.summary || '',
        entry.category || '未分类',
        toTags(entry.tags),
        entry.color || 'purple',
        content,
        entry.author || '小陶老师',
        entry.source || '',
        entry.estimated_read_time || '5 分钟',
        publishedAt,
      ]
    );

    if (r.rows[0].inserted) { inserted++; console.log(`  + ${id} ${slug}`); }
    else { updated++; }
  }

  // 清掉不在清单里的旧行（早先 seed 进来的那批 slug 是文件名的重复数据）
  const { rowCount: removed } = await pool.query(
    `DELETE FROM articles WHERE NOT (id = ANY($1::int[]))`, [ids]
  );
  if (removed) console.log(`🧹 删除清单外的旧行 ${removed} 条`);

  // 序列推进到当前最大 id，避免以后插入撞主键
  await pool.query(
    `SELECT setval('articles_id_seq', GREATEST((SELECT MAX(id) FROM articles), 1))`
  );

  const { rows } = await pool.query(
    `SELECT count(*)::int AS n FROM articles WHERE is_published = true`
  );
  console.log(`\n📊 新增 ${inserted} · 更新 ${updated} · 缺正文 ${missingFile} · 删除旧行 ${removed}`);
  console.log(`📊 数据库现有已发布文章 ${rows[0].n} 篇`);
  process.exit(0);
}

main().catch((e) => {
  console.error('❌ 同步失败:', e);
  process.exit(1);
});
