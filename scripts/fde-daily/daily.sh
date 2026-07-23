#!/bin/bash
# FDE 每日抓取 + AI 重写 + 自动审核 + 自动发布
# 执行时间：每天 08:00（cron）
set -e
SITE_DIR="/root/.openclaw/workspace/projects/maxkb-course-site/site"
SCRIPTS_DIR="$SITE_DIR/scripts/fde-daily"
export MINIMAX_API_KEY="${MINIMAX_API_KEY}"

echo "═══════════════════════════════════"
echo "📡 FDE 每日内容运营 · $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════"

echo "【1/3】抓取 FDE 文章..."
python3 "$SCRIPTS_DIR/fetch_articles.py"

echo ""
echo "【2/3】AI 重写 5 篇..."
python3 "$SCRIPTS_DIR/rewrite_articles.py"

echo ""
echo "【3/3】AI 自动审核 + 自动发布..."
python3 "$SCRIPTS_DIR/auto_review_and_publish.py"

echo ""
echo "═══════════════════════════════════"
echo "✅ 每日抓取完成"
echo "═══════════════════════════════════"
