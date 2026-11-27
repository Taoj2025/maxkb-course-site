#!/bin/bash
# Vercel Ignored Build Step —— 判断这次提交要不要重新构建静态快照
#
# 用法（Vercel 自动调用，不要手动跑）：
#   bash scripts/ignore-build.sh
#
# 退出码约定（Vercel 的语义）：
#   0 = 跳过构建（部署被标记为 CANCELED）
#   1 = 照常构建
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
# ⚠️ 不能用 `git diff HEAD^ HEAD`：Vercel 每次 push 只构建最后一个 commit，
#    HEAD^ 可能不是上次部署的那个。用 VERCEL_GIT_PREVIOUS_SHA 才对。

set -uo pipefail

PREV="${VERCEL_GIT_PREVIOUS_SHA:-}"
CURR="${VERCEL_GIT_COMMIT_SHA:-}"

# 这些路径走 rewrites 实时转发，不进静态快照 —— 只有它们变了就跳过构建
readonly EXCLUDES=(
  ':(exclude)data'
  ':(exclude)articles'
  ':(exclude)articles.json'
  ':(exclude).audit'
)

# 拿不到 SHA 或 git 不可用 → 老老实实构建
if [ -z "$PREV" ] || [ -z "$CURR" ]; then
  echo "no git shas — building to be safe"
  exit 1
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "not a git checkout — building to be safe"
  exit 1
fi

echo "ignore-build: prev=${PREV:0:7} curr=${CURR:0:7}"

# ── 主路径：PREV 在克隆里，直接 diff ──
#
# ⚠️ 必须检查 git diff 的退出码：diff 失败时输出是空的，
#    而「空」在下面会被当成「没变化 → 跳过构建」——
#    那会导致该更新的 HTML 没更新。所以失败时一律走构建。
diff_files() {
  git diff --name-only "$1" "$2" -- . "${EXCLUDES[@]}" 2>/dev/null
}

if git cat-file -e "$PREV^{commit}" 2>/dev/null; then
  if ! CHANGED=$(diff_files "$PREV" "$CURR"); then
    echo "git diff failed — building to be safe"
    exit 1
  fi
  if [ -z "$CHANGED" ]; then
    echo "only data/articles changed since ${PREV:0:7} — skipping build"
    exit 0
  fi
  echo "shell changed since ${PREV:0:7} — building:"
  echo "$CHANGED" | head -20
  exit 1
fi

# ── 兜底：PREV 不在克隆里 ──
#
# Vercel 用 `git clone --depth=10` 克隆，上一次部署的 commit
# 很可能已经被截断掉了（内容机器人半小时推一次，10 个 commit 也就 5 小时）。
#
# 先试试能不能单独把那个 commit 拉下来。
if git fetch --depth=1 origin "$PREV" >/dev/null 2>&1 &&
   git cat-file -e "$PREV^{commit}" 2>/dev/null; then
  if ! CHANGED=$(diff_files "$PREV" "$CURR"); then
    echo "git diff failed after fetch — building to be safe"
    exit 1
  fi
  if [ -z "$CHANGED" ]; then
    echo "only data/articles changed since ${PREV:0:7} (fetched) — skipping build"
    exit 0
  fi
  echo "shell changed since ${PREV:0:7} — building:"
  echo "$CHANGED" | head -20
  exit 1
fi

# ── 最后兜底：浅克隆里根本没有那个 commit ──
#
# 这时退一步，比较「克隆里能拿到的最早那个 commit」和当前 commit 的
# **外壳文件内容**。
#
# 为什么这样判：
#   外壳改动一定会触发一次构建，构建成功 = 外壳已上线。
#   所以只要克隆窗口内外壳内容没变过，说明外壳自从上次上线就没动过 → 跳过。
#   如果窗口内有外壳改动 → 构建（哪怕算不清具体差异）。
#
# 比内容而不是比文件名：初始提交会把所有文件都「新增」一遍，
# 按文件名判会把这种一次性新增误当成「外壳变了」。
OLDEST=$(git rev-list --max-parents=0 HEAD 2>/dev/null | tail -1)
if [ -z "$OLDEST" ]; then
  echo "cannot determine history — building to be safe"
  exit 1
fi

if ! CHANGED=$(git diff --name-only "$OLDEST" "$CURR" -- . "${EXCLUDES[@]}" 2>/dev/null); then
  echo "git diff failed — building to be safe"
  exit 1
fi

if [ -z "$CHANGED" ]; then
  echo "shell unchanged across available history — skipping build"
  exit 0
fi

echo "shell changed within available history — building:"
echo "$CHANGED" | head -20
exit 1
