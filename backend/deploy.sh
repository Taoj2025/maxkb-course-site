#!/usr/bin/env bash
# MaxKB FDE 后端部署脚本 · 服务器侧
# 用法：在 /opt/maxkb-api 目录下由 GitHub Actions SSH 触发，或手动 bash deploy.sh
#
# 自 chmod（首次部署可能没有 +x）
[ -x "$0" ] || chmod +x "$0" 2>/dev/null || true
#
# 首次部署步骤（在服务器上）：
#   1. sudo mkdir -p /opt/maxkb-api && sudo chown $USER:$USER /opt/maxkb-api
#   2. cd /opt/maxkb-api && git clone <your-repo-url> .
#   3. 手动创建 backend/.env（参考 backend/.env.example）
#      必须设置：PGPASSWORD / JWT_SECRET / ADMIN_DEFAULT_PASSWORD
#   4. cd backend && docker compose up -d
#   5. bash backend/deploy.sh  # 后续每次自动部署

set -euo pipefail

# ============ 路径配置 ============
APP_DIR="/opt/maxkb-api"
BACKEND_DIR="$APP_DIR/backend"
COMPOSE_FILE="$BACKEND_DIR/docker-compose.yml"

LOG_PREFIX="[maxkb-deploy]"

echo "$LOG_PREFIX $(date '+%Y-%m-%d %H:%M:%S') 开始部署..."

# ============ 1. 健康前置检查 ============
if ! command -v docker >/dev/null 2>&1; then
  echo "$LOG_PREFIX ❌ docker 未安装，请先安装 Docker"
  exit 1
fi
if ! command -v git >/dev/null 2>&1; then
  echo "$LOG_PREFIX ❌ git 未安装"
  exit 1
fi

# ============ 2. 首次克隆 ============
if [ ! -d "$APP_DIR/.git" ]; then
  echo "$LOG_PREFIX 📦 首次克隆仓库..."
  # 优先用 HTTPS，避免 SSH key 配错（GitHub Actions 用的同一把 key 可访问）
  if [ -z "${REPO_URL:-}" ]; then
    echo "$LOG_PREFIX ❌ 未设置 REPO_URL 环境变量"
    echo "  请设置：export REPO_URL=https://github.com/你的用户名/maxkb-course-site.git"
    exit 1
  fi
  git clone "$REPO_URL" "$APP_DIR"
fi

# ============ 3. 拉取最新代码 ============
cd "$APP_DIR"
echo "$LOG_PREFIX 🔄 拉取最新代码..."
git fetch origin
git reset --hard origin/main

# ============ 4. 检查 .env ============
if [ ! -f "$BACKEND_DIR/.env" ]; then
  echo "$LOG_PREFIX ⚠️ backend/.env 不存在"
  echo "  请手动创建：cp $BACKEND_DIR/.env.example $BACKEND_DIR/.env && nano $BACKEND_DIR/.env"
  echo "  必须设置：PGPASSWORD / JWT_SECRET / ADMIN_DEFAULT_PASSWORD"
  exit 1
fi

# ============ 5. Docker Compose 重启 ============
cd "$BACKEND_DIR"
echo "$LOG_PREFIX 🐳 重启 Docker Compose 服务..."
docker compose pull 2>/dev/null || true   # 镜像不存在时忽略
docker compose up -d --remove-orphans

# ============ 6. 健康检查 ============
echo "$LOG_PREFIX ⏳ 等待服务启动..."
sleep 8

HEALTH_URL="http://127.0.0.1:3001/api/health"
if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
  echo "$LOG_PREFIX ✅ 部署成功 · 健康检查通过"
  curl -fsS "$HEALTH_URL"
  echo ""
  echo "$LOG_PREFIX 📊 服务状态："
  docker compose ps
else
  echo "$LOG_PREFIX ❌ 健康检查失败，查看最近日志："
  docker compose logs --tail=80 api
  exit 1
fi

# ============ 7. 清理旧镜像 ============
echo "$LOG_PREFIX 🧹 清理悬空镜像..."
docker image prune -f >/dev/null 2>&1 || true

# ============ 8. SSL 证书自动续期（certbot）============
if command -v certbot >/dev/null 2>&1; then
  echo "$LOG_PREFIX 🔒 检查 SSL 证书续期..."
  if certbot renew --quiet --deploy-hook "systemctl reload nginx"; then
    echo "$LOG_PREFIX ✅ SSL 证书已检查/续期"
  else
    echo "$LOG_PREFIX ⚠️ certbot 续期失败（不影响本次部署，证书由 systemd timer 自动续期）"
  fi
else
  echo "$LOG_PREFIX ℹ️ certbot 未安装，跳过 SSL 续期检查"
fi

echo "$LOG_PREFIX 🎉 部署完成 · $(date '+%Y-%m-%d %H:%M:%S')"