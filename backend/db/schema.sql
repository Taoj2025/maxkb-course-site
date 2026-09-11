-- ==========================================================
-- MaxKB FDE 教学站 · PostgreSQL Schema
-- 数据库：postgres · 主机：119.91.234.159:5432 · 用户：postgres
-- 由 Claude Code 为小陶老师生成 · 2026-09-11
-- ==========================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()

-- ---------- 1. 用户/会员表 ----------
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,                              -- bcrypt
    role            TEXT NOT NULL DEFAULT 'user',               -- user / admin
    plan_id         TEXT NOT NULL DEFAULT 'free',               -- free / standard / flagship
    status          TEXT NOT NULL DEFAULT 'active',             -- active / expired / banned
    joined_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    upgraded_at     TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    total_downloads INTEGER NOT NULL DEFAULT 0,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_email   ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_plan    ON users(plan_id);
CREATE INDEX IF NOT EXISTS idx_users_status  ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_expires ON users(expires_at);

-- ---------- 2. 课程章节表（替代 assets/js/data.js 的 chapters 数组）----------
CREATE TABLE IF NOT EXISTS chapters (
    id          SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    description TEXT NOT NULL,
    icon        TEXT NOT NULL DEFAULT '📘',
    tag         TEXT NOT NULL DEFAULT 'theory',                 -- theory / practice / scene
    duration    TEXT,
    pages       TEXT,
    outputs     TEXT[],
    sort_order  INTEGER NOT NULL DEFAULT 0,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------- 3. 文章表（替代 articles.json + articles/*.md）----------
CREATE TABLE IF NOT EXISTS articles (
    id          SERIAL PRIMARY KEY,
    slug        TEXT UNIQUE NOT NULL,
    title       TEXT NOT NULL,
    summary     TEXT,
    category    TEXT NOT NULL DEFAULT '未分类',
    tags        TEXT[],
    color       TEXT DEFAULT 'purple',
    content_md  TEXT,
    cover_url   TEXT,
    author      TEXT DEFAULT '小陶老师',
    source      TEXT,
    source_url  TEXT,
    estimated_read_time TEXT DEFAULT '5 分钟',
    view_count  INTEGER NOT NULL DEFAULT 0,
    is_published BOOLEAN NOT NULL DEFAULT TRUE,
    published_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_articles_slug      ON articles(slug);
CREATE INDEX IF NOT EXISTS idx_articles_category  ON articles(category);
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_tags      ON articles USING GIN(tags);

-- ---------- 4. 资源表（替代 downloads/ 文件名映射）----------
CREATE TABLE IF NOT EXISTS resources (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug            TEXT UNIQUE NOT NULL,                      -- 静态文件名（与 downloads/ 一致）
    title           TEXT NOT NULL,
    description     TEXT,
    file_size       BIGINT,
    min_plan        TEXT NOT NULL DEFAULT 'standard',          -- free / standard / flagship
    download_count  INTEGER NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------- 5. 下载记录 ----------
CREATE TABLE IF NOT EXISTS downloads (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID REFERENCES users(id) ON DELETE SET NULL,
    resource_id   UUID REFERENCES resources(id) ON DELETE SET NULL,
    ip_address    INET,
    user_agent    TEXT,
    referer       TEXT,
    downloaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_downloads_user     ON downloads(user_id);
CREATE INDEX IF NOT EXISTS idx_downloads_resource ON downloads(resource_id);
CREATE INDEX IF NOT EXISTS idx_downloads_time     ON downloads(downloaded_at DESC);

-- ---------- 6. 联系留言（替代 Formspree）----------
CREATE TABLE IF NOT EXISTS contact_messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT,
    email       TEXT,
    phone       TEXT,
    company     TEXT,
    subject     TEXT,
    message     TEXT NOT NULL,
    source      TEXT DEFAULT 'index',                          -- index / trial / enterprise / contact
    status      TEXT NOT NULL DEFAULT 'new',                   -- new / read / replied / archived
    ip_address  INET,
    user_agent  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_contact_status ON contact_messages(status);
CREATE INDEX IF NOT EXISTS idx_contact_time   ON contact_messages(created_at DESC);

-- ---------- 7. AI 热点（替代 data/aihot.json）----------
CREATE TABLE IF NOT EXISTS aihot_items (
    id          SERIAL PRIMARY KEY,
    category    TEXT NOT NULL DEFAULT 'general',               -- general / fde
    title       TEXT NOT NULL,
    url         TEXT,
    summary     TEXT,
    source      TEXT,
    hot_score   INTEGER DEFAULT 0,
    rank        INTEGER,
    fetched_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_aihot_cat  ON aihot_items(category);
CREATE INDEX IF NOT EXISTS idx_aihot_rank ON aihot_items(category, rank);

-- ---------- 8. 管理员操作日志 ----------
CREATE TABLE IF NOT EXISTS admin_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_email     TEXT NOT NULL,
    action          TEXT NOT NULL,                             -- upgrade_user / ban_user / ...
    target_type     TEXT,
    target_id       TEXT,
    details         JSONB,
    ip_address      INET,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_admin_logs_admin ON admin_logs(admin_email);
CREATE INDEX IF NOT EXISTS idx_admin_logs_time  ON admin_logs(created_at DESC);

-- ---------- 9. updated_at 触发器 ----------
CREATE OR REPLACE FUNCTION trg_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS users_updated_at    ON users;
DROP TRIGGER IF EXISTS articles_updated_at ON articles;
CREATE TRIGGER users_updated_at    BEFORE UPDATE ON users    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();
CREATE TRIGGER articles_updated_at BEFORE UPDATE ON articles FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();
