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

# 3.1 npm 走国内镜像，node-gyp 编译 bcrypt 时也要能拿到 node 头文件。
#     服务器在境内，直连 nodejs.org 会一直挂着不返回（曾导致部署卡死 10 分钟超时）。
export npm_config_disturl="${npm_config_disturl:-https://npmmirror.com/mirrors/node}"
export npm_config_registry="${npm_config_registry:-https://mirrors.tencent.com/npm/}"
export npm_config_fetch_retries="${npm_config_fetch_retries:-3}"
export npm_config_fetch_timeout="${npm_config_fetch_timeout:-120000}"

# 3.2 用 npm install 而不是 npm ci。
#     npm ci 会先删掉整个 node_modules 再重装 → 每次部署都要重新编译 bcrypt 等
#     原生模块，而原生模块的编译/下载在境内极慢甚至挂死，失败后服务就是坏的。
#     npm install 会复用已装好的包（含已编译的 .node），只在缺包时才补。
#
#     --ignore-scripts：跳过所有 install 脚本（node-pre-gyp / node-gyp），
#     这是部署卡死的根因。本项目唯一的原生依赖是 bcrypt，由下面的
#     ensure_bcrypt() 显式处理，其余依赖（express / pg / helmet…）都是纯 JS。
npm install --omit=dev --no-audit --no-fund --prefer-offline --ignore-scripts

# 3.3 bcrypt 是唯一的原生依赖，必须确认它真的能加载，否则重启就会把 API 打挂。
#     装不上时直接拉官方预编译二进制兜底（napi-v3，linux-x64-glibc）。
ensure_bcrypt() {
  if node -e 'import("bcrypt").then(()=>process.exit(0)).catch(()=>process.exit(1))' 2>/dev/null; then
    return 0
  fi
  log "⚠️  bcrypt 原生模块加载失败，尝试安装官方预编译二进制…"
  local ver url tmp
  ver=$(node -e 'import("node:fs").then(fs=>console.log(JSON.parse(fs.readFileSync("./node_modules/bcrypt/package.json","utf8")).version)).catch(()=>process.exit(1))' 2>/dev/null || echo "")
  [ -n "$ver" ] || ver="5.1.1"
  url="https://github.com/kelektiv/node.bcrypt.js/releases/download/v${ver}/bcrypt_lib-v${ver}-napi-v3-linux-x64-glibc.tar.gz"
  tmp=$(mktemp -d)
  if curl -fsSL --max-time 120 -o "$tmp/bc.tar.gz" "$url" \
     && tar -xzf "$tmp/bc.tar.gz" -C "$tmp" \
     && mkdir -p node_modules/bcrypt/lib/binding/napi-v3 \
     && cp "$tmp"/napi-v3/bcrypt_lib.node node_modules/bcrypt/lib/binding/napi-v3/bcrypt_lib.node; then
    log "✅ bcrypt 预编译二进制已就位"
  else
    rm -rf "$tmp"
    log "❌ bcrypt 安装失败，中止部署（不重启服务，避免把线上 API 打挂）"
    return 1
  fi
  rm -rf "$tmp"
  node -e 'import("bcrypt").then(()=>process.exit(0)).catch(()=>process.exit(1))' 2>/dev/null || {
    log "❌ bcrypt 仍无法加载，中止部署"
    return 1
  }
  return 0
}

ensure_bcrypt || exit 1

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
