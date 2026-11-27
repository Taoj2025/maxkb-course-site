#!/bin/bash
# Vercel Ignored Build Step —— 判断这次提交要不要重新构建静态快照
#
# 用法（Vercel 自动调用，不要手动跑）：
#   bash scripts/ignore-build.sh
#
# 约定：退出码 0 = 跳过构建，退出码非 0 = 照常构建。
#
# ── 为什么需要这个 ──
#
# 站点是「静态快照 + 实时转发」架构：
#   data/ articles/ articles.json  → 走 vercel.json 的 rewrites 实时转发源站
#   HTML 外壳（*.html assets/ api/ proxy.js）→ 才是 Vercel 静态快照的内容
#
# 内容机器人每 30 分钟推一次（热点 + 招聘数据），一天 40+ 次。
# 每次 push 都触发一次 Vercel 部署 —— 但那些提交**只改 data/ articles/**，
# 快照内容一个字节都没变，纯属白烧 Hobby 每天 100 次的部署配额
# （而且配额是团队级共用的，见 VERCEL-DEPLOY.md 坑五）。
#
# 所以这里只在「HTML 外壳真的变了」时才让 Vercel 构建。
#
# ── 判定方式 ──
#
# 用 Vercel 注入的两个 SHA 算 diff：
#   VERCEL_GIT_PREVIOUS_SHA  上一次部署的 commit
#   VERCEL_GIT_COMMIT_SHA    这次要部署的 commit
#
# 排除掉只影响实时转发内容的路径后，diff 为空 = 快照没变 = 跳过构建。
#
# ⚠️ 两个 SHA 拿不到时（CLI 部署、没有 git 历史的环境）一律「构建」，
#    宁可多构建一次，也不要出现「该更新的没更新」。

set -uo pipefail

PREV="${VERCEL_GIT_PREVIOUS_SHA:-}"
CURR="${VERCEL_GIT_COMMIT_SHA:-}"

# 拿不到 SHA 或 git 不可用 → 老老实实构建
if [ -z "$PREV" ] || [ -z "$CURR" ]; then
  echo "no git shas — building to be safe"
  exit 1
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "not a git checkout — building to be safe"
  exit 1
fi

# diff 拿不出来（比如浅克隆里没有那个 commit）→ 也要构建
if ! git cat-file -e "$PREV^{commit}" 2>/dev/null; then
  echo "previous sha not available — building to be safe"
  exit 1
fi
if ! git cat-file -e "$CURR^{commit}" 2>/dev/null; then
  echo "current sha not available — building to be safe"
  exit 1
fi

# 只看会进快照的路径。data/ articles/ 走 rewrites 实时转发，不进快照。
#
# ⚠️ 必须检查 git diff 的退出码：diff 失败时输出是空的，
#    而「空」在下面会被当成「没变化 → 跳过构建」——
#    那会导致该更新的 HTML 没更新。所以失败时一律走构建。
if ! CHANGED=$(git diff --name-only "$PREV" "$CURR" -- . \
  ':(exclude)data' \
  ':(exclude)articles' \
  ':(exclude)articles.json' \
  ':(exclude).audit' 2>/dev/null); then
  echo "git diff failed — building to be safe"
  exit 1
fi

if [ -z "$CHANGED" ]; then
  echo "only data/articles changed — skipping build"
  exit 0
fi

echo "shell changed — building:"
echo "$CHANGED" | head -20
exit 1
