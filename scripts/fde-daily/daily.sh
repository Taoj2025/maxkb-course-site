#!/bin/bash
# FDE 每日抓取 + AI 重写 + 推送脚本
# 执行时间：每天 09:00（cron）

set -e
SITE_DIR="/root/.openclaw/workspace/projects/maxkb-course-site/site"
SCRIPTS_DIR="$SITE_DIR/scripts/fde-daily"
export MINIMAX_API_KEY="${MINIMAX_API_KEY}"
export AIBOX_API_KEY="${AIBOX_API_KEY}"

echo "═══════════════════════════════════"
echo "📡 FDE 每日内容运营 · $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════"

# 1. 抓取
echo "【1/3】抓取 FDE 文章..."
python3 "$SCRIPTS_DIR/fetch_articles.py"

# 2. AI 重写
echo ""
echo "【2/3】AI 重写 5 篇..."
python3 "$SCRIPTS_DIR/rewrite_articles.py"

# 3. 推送审核（待您确认后发布）
echo ""
echo "【3/3】生成推送审核提醒..."
PENDING_FILE=$(ls -t /root/.openclaw/workspace/projects/maxkb-course-site/fde-pending/pending_*.json | head -1)
if [ -f "$PENDING_FILE" ]; then
  echo ""
  echo "✅ 待审核内容已生成："
  echo "  $PENDING_FILE"
  echo ""
  echo "  您可以："
  echo "  - cat $PENDING_FILE | jq '.[].title'"
  echo "  - 打开文件查看完整内容"
  echo ""
  echo "  审核通过后运行："
  echo "  - python3 $SCRIPTS_DIR/publish_pending.py"
fi

echo ""
echo "═══════════════════════════════════"
echo "✅ 每日抓取完成"
echo "═══════════════════════════════════"
