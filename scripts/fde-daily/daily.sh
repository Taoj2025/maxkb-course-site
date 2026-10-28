#!/bin/bash
# FDE 内容运营机器人
#
# 用法：
#   bash scripts/fde-daily/daily.sh aihot     只刷新 AI 热点（轻量，适合每小时跑）
#   bash scripts/fde-daily/daily.sh articles  只跑文章管线（抓取→重写→审核→发布）
#   bash scripts/fde-daily/daily.sh all       全部都跑（默认）
#
# 环境变量：
#   SITE_DIR  站点根目录（默认 /var/www/maxkb-course-site）
#   WORK_DIR  中间产物目录（默认 openclaw 工作区）
#
# 发布走 scripts/publish-site.sh（git SSH 推送，不需要 GitHub token）。
set -uo pipefail

SITE_DIR="${SITE_DIR:-/var/www/maxkb-course-site}"
WORK_DIR="${WORK_DIR:-/root/.openclaw/workspace/projects/maxkb-course-site}"
BACKEND_DIR="${BACKEND_DIR:-/opt/maxkb-api/backend}"
SCRIPTS_DIR="$SITE_DIR/scripts/fde-daily"
MODE="${1:-all}"
export SITE_DIR WORK_DIR

mkdir -p "$WORK_DIR/fde-candidates" "$WORK_DIR/fde-pending"

echo "═══════════════════════════════════"
echo "📡 FDE 内容运营 · $(date '+%Y-%m-%d %H:%M:%S') · 模式=${MODE}"
echo "   SITE_DIR=${SITE_DIR}"
echo "═══════════════════════════════════"

run_aihot() {
  echo ""
  echo "【AI 热点】刷新 aihot.virxact.com RSS…"
  python3 "$SITE_DIR/scripts/fetch-aihot.py" || {
    echo "⚠️  AI 热点抓取失败，保留旧数据"
    return 0
  }
  echo "【AI 热点】推送到 GitHub…"
  bash "$SITE_DIR/scripts/publish-site.sh" \
    "auto: 刷新 AI 热点 · $(date '+%Y-%m-%d %H:%M')" || true

  # /api/aihot 读的是数据库，得跟着一起刷，否则接口一直返回几个月前的旧热点
  if [ -d "$BACKEND_DIR" ]; then
    (cd "$BACKEND_DIR" && npm run --silent db:import-aihot) \
      || echo "⚠️  热点入库失败（静态 JSON 不受影响）"
  fi
}

run_articles() {
  echo ""
  echo "【1/4】抓取 FDE 文章..."
  python3 "$SCRIPTS_DIR/fetch_articles.py"

  echo ""
  echo "【2/4】AI 重写…"
  python3 "$SCRIPTS_DIR/rewrite_articles.py"

  echo ""
  echo "【3/4】AI 自动审核 + 自动发布…"
  python3 "$SCRIPTS_DIR/auto_review_and_publish.py"

  echo ""
  echo "【4/4】同步文章清单到数据库…"
  # articles.json 是文章的唯一真相，/api/articles 读的是数据库。
  # 不同步的话，首页资讯会继续显示旧列表，点进去全是 404。
  if [ -d "$BACKEND_DIR" ]; then
    (cd "$BACKEND_DIR" && npm run --silent db:import-articles) \
      || echo "⚠️  数据库同步失败（站点文章列表仍可正常访问）"
  else
    echo "   （跳过：没找到后端目录 $BACKEND_DIR）"
  fi
}

case "$MODE" in
  aihot)    run_aihot ;;
  articles) run_articles ;;
  all)      run_aihot; run_articles ;;
  *)        echo "未知模式：$MODE（可选 aihot / articles / all）"; exit 1 ;;
esac

echo ""
echo "═══════════════════════════════════"
echo "✅ 完成 · $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════"
