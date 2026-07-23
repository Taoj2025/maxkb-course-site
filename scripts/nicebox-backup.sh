#!/bin/bash
# nicebox-site-manager 自动备份脚本
# 每周日 23:00 同步 nicebox 内容到 GitHub 仓库

set -e
BACKUP_DIR="/root/.openclaw/workspace/projects/maxkb-course-site/nicebox-backup"
GITHUB_REPO="Taoj2025/maxkb-course-site"
GITHUB_TOKEN="${GITHUB_PAT_TOKEN}"  # 占位符，需在执行环境设置
SITE_ID=1151
API_BASE="https://ai.nicebox.cn/api/openclaw"

# 1. 创建备份目录
mkdir -p "$BACKUP_DIR/articles"
mkdir -p "$BACKUP_DIR/logs"

# 2. 备份时间戳
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 3. 导出站点状态
echo "📊 备份站点状态..."
curl -s -H "Authorization: $AIBOX_API_KEY" \
  "$API_BASE/site/status" \
  > "$BACKUP_DIR/site_status_$TIMESTAMP.json"

# 4. 导出所有留言
echo "💬 备份留言列表..."
PAGE=1
while true; do
  RESP=$(curl -s -H "Authorization: $AIBOX_API_KEY" \
    "$API_BASE/message/getlist?page=$PAGE&page_size=50")
  echo "$RESP" > "$BACKUP_DIR/messages_p${PAGE}_$TIMESTAMP.json"
  
  # 检查是否还有更多
  HAS_NEXT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print('1' if d['response']['data']['pagination']['page']*d['response']['data']['pagination']['page_size'] < d['response']['data']['pagination']['total'] else '0')" 2>/dev/null || echo "0")
  
  if [ "$HAS_NEXT" = "0" ]; then
    break
  fi
  PAGE=$((PAGE+1))
done

# 5. 写入备份日志
echo "📝 备份日志..."
cat > "$BACKUP_DIR/logs/backup_$TIMESTAMP.log" << EOF
[$(date '+%Y-%m-%d %H:%M:%S')] nicebox 自动备份完成
- 站点 ID: $SITE_ID
- API Base: $API_BASE
- 备份路径: $BACKUP_DIR
- 备份内容: site_status + messages + 后续添加文章导出
EOF

# 6. 推送到 GitHub（可选）
echo "🚀 推送备份到 GitHub..."
cd "$BACKUP_DIR"
git init -q 2>/dev/null || true
git add -A
git commit -m "chore: nicebox 自动备份 $TIMESTAMP" -q 2>/dev/null || true

# 7. 清理 90 天前的备份
echo "🧹 清理过期备份..."
find "$BACKUP_DIR" -name "*.json" -mtime +90 -delete 2>/dev/null
find "$BACKUP_DIR/logs" -name "*.log" -mtime +90 -delete 2>/dev/null

echo "✅ nicebox 自动备份完成: $TIMESTAMP"
ls -la "$BACKUP_DIR/"
