#!/usr/bin/env bash
# 站点数据发布 · 提交并推送到 GitHub
#
# 用法：
#   SITE_DIR=/var/www/maxkb-course-site bash scripts/publish-site.sh "auto: 说明"
#
# 为什么用 git 而不是 GitHub API：
#   原来的 auto_review_and_publish.py / push_fde_data.py 走 GitHub Contents API，
#   需要 GITHUB_PAT_TOKEN，而服务器上没有这个 token → 推送永远 401，数据发不出去。
#   服务器的 git 仓库已经配好 SSH key（git@github.com:Taoj2025/maxkb-course-site.git），
#   直接 git push 就行，不需要任何凭据。
#
# 推上去之后，GitHub Actions 会把 main 分支同步到服务器 web root 和 GitHub Pages，
# latest.html 随之更新。
set -euo pipefail

SITE_DIR="${SITE_DIR:-/var/www/maxkb-course-site}"
BRANCH="${BRANCH:-main}"
MESSAGE="${1:-auto: 更新站点数据 $(date '+%Y-%m-%d %H:%M')}"
LOCK_FILE="/tmp/maxkb-publish.lock"

log() { echo "[publish-site] $*"; }

# ── 并发保护：同一时刻只跑一个发布任务 ──
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  log "已有发布任务在运行，本次跳过"
  exit 0
fi

[ -d "$SITE_DIR/.git" ] || { log "❌ 不是 git 仓库：$SITE_DIR"; exit 1; }

cd "$SITE_DIR"
git config --global --add safe.directory "$SITE_DIR" 2>/dev/null || true

# ── 只提交内容数据，不碰代码 ──
git add -- data/aihot.json data/aihot-fde.json articles.json articles/ 2>/dev/null || true

if git diff --cached --quiet; then
  log "无内容变更，跳过提交"
  exit 0
fi

CHANGED=$(git diff --cached --name-only | tr '\n' ' ')
log "待提交：$CHANGED"

git commit -m "$MESSAGE" >/dev/null
log "已提交 $(git rev-parse --short HEAD)"

# ── 推送（失败则 rebase 后重试一次）────
if git push origin "HEAD:$BRANCH" 2>&1; then
  log "✅ 推送成功 → origin/$BRANCH"
  exit 0
fi

log "推送失败，尝试 rebase 后重试…"
git pull --rebase origin "$BRANCH" >/dev/null 2>&1 || true
if git push origin "HEAD:$BRANCH" 2>&1; then
  log "✅ rebase 后推送成功 → origin/$BRANCH"
  exit 0
fi

log "❌ 推送失败，请检查网络 / SSH key"
exit 1
