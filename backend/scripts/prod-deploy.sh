#!/usr/bin/env bash
# MaxKB FDE 后端 · 生产部署脚本（服务器侧）
#
# 由 .github/workflows/deploy-backend.yml 通过 SSH 调用，也可手动执行：
#   bash backend/scripts/prod-deploy.sh
#
# 做的事：
#   1. 从 git 仓库同步 backend/ → /opt/maxkb-api/backend（保留 .env / node_modules）
#   2. 安装依赖
#   3. 执行幂等数据库迁移（建表 + 种子数据）
#   4. 重启 systemd 服务并做健康检查
#
# 设计要点：
#   - 应用目录在 nginx web root 之外，避免 .env / 源码被公网下载
#   - rsync --delete 会删掉服务器上的多余文件，但 .env 和 node_modules 被 exclude 保护
#   - 迁移脚本全部是幂等的（CREATE TABLE IF NOT EXISTS / ON CONFLICT DO NOTHING），
#     重复执行不会破坏现有数据

set -euo pipefail

REPO_DIR="${REPO_DIR:-/var/www/maxkb-course-site}"
APP_DIR="${APP_DIR:-/opt/maxkb-api}"
BACKEND_DIR="$APP_DIR/backend"
SERVICE="${SERVICE:-maxkb-api}"
HEALTH_URL="http://127.0.0.1:3001/api/health"
LOG_PREFIX="[maxkb-deploy]"

log() { echo "$LOG_PREFIX $*"; }

# ============ 0. 前置检查 ============
[ -d "$REPO_DIR/.git" ] || { log "❌ 仓库不存在: $REPO_DIR"; exit 1; }
command -v rsync  >/dev/null 2>&1 || { log "❌ rsync 未安装";  exit 1; }
command -v npm    >/dev/null 2>&1 || { log "❌ npm 未安装";    exit 1; }
command -v node   >/dev/null 2>&1 || { log "❌ node 未安装";   exit 1; }

log "开始部署 $(date '+%Y-%m-%d %H:%M:%S')"

# ============ 1. 拉取最新代码 ============
cd "$REPO_DIR"
git config --global --add safe.directory "$REPO_DIR" 2>/dev/null || true
log "拉取最新代码…"
git pull --ff-only origin main
log "当前 HEAD: $(git log -1 --oneline)"

# ============ 2. 同步 backend/ → 应用目录 ============
log "同步 backend/ → $BACKEND_DIR"
mkdir -p "$BACKEND_DIR"
rsync -a --delete \
      --exclude node_modules/ \
      --exclude .env \
      --exclude .pgdata/ \
      --exclude .logs/ \
      "$REPO_DIR/backend/" "$BACKEND_DIR/"

# 资源与文章目录用软链指回仓库，服务器上只有一份
ln -sfn "$REPO_DIR/articles"  "$APP_DIR/articles"
ln -sfn "$REPO_DIR/downloads" "$APP_DIR/downloads"

# .env 是本机配置，不随代码更新；缺失时用模板兜底
if [ ! -f "$BACKEND_DIR/.env" ]; then
  log "⚠️  $BACKEND_DIR/.env 不存在，用 .env.example 生成占位版本"
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  log "   ⚠️ 必须手动填入 PGPASSWORD / JWT_SECRET / ADMIN_DEFAULT_PASSWORD 后重启"
fi
chown www-data:www-data "$BACKEND_DIR/.env"
chmod 600 "$BACKEND_DIR/.env"

# ============ 3. 安装依赖 ============
log "安装依赖…"
cd "$BACKEND_DIR"
npm ci --omit=dev --no-audit --no-fund

# ============ 4. 数据库迁移（幂等）============
log "执行数据库迁移…"
npm run --silent db:schema
npm run --silent db:seed

# 管理员账号只做检查、不自动重置 —— 避免覆盖用户自己改过的密码。
# 需要重置时手动执行： cd /opt/maxkb-api/backend && npm run init:admin
env_get() { grep -m1 "^$1=" "$BACKEND_DIR/.env" | cut -d= -f2-; }
ADMIN_ROWS=$(PGPASSWORD="$(env_get PGPASSWORD)" \
  psql -h "$(env_get PGHOST)" -p "$(env_get PGPORT)" -U "$(env_get PGUSER)" \
       -d "$(env_get PGDATABASE)" -tAc \
  "select count(*) from users where role='admin' and password_hash <> '__INIT_VIA_SCRIPT__'" 2>/dev/null || echo "")
if [ "$ADMIN_ROWS" = "0" ] || [ -z "$ADMIN_ROWS" ]; then
  log "⚠️  管理员账号未初始化或仍是占位密码，请手动执行： npm run init:admin"
fi

# AI 热点表：只在空表时从静态 JSON 灌一次，避免每次部署都重写
AIHOT_ROWS=$(PGPASSWORD="$(env_get PGPASSWORD)" \
  psql -h "$(env_get PGHOST)" -p "$(env_get PGPORT)" -U "$(env_get PGUSER)" \
       -d "$(env_get PGDATABASE)" -tAc \
  "select count(*) from aihot_items" 2>/dev/null || echo "")
if [ "$AIHOT_ROWS" = "0" ]; then
  log "AI 热点表为空，从静态 JSON 导入…"
  npm run --silent db:import-aihot
fi

# ============ 5. 重启服务 ============
log "重启 systemd 服务…"
systemctl restart "$SERVICE"

# ============ 6. 健康检查 ============
log "等待服务启动…"
for i in $(seq 1 15); do
  sleep 2
  if curl -fsS --max-time 5 "$HEALTH_URL" >/dev/null 2>&1; then
    log "✅ 部署成功 · 健康检查通过"
    curl -fsS "$HEALTH_URL"; echo
    systemctl --no-pager --lines=0 status "$SERVICE" | head -5
    exit 0
  fi
done

log "❌ 健康检查失败，服务日志："
journalctl -u "$SERVICE" --no-pager --lines=50
exit 1
