#!/bin/bash
# 生成 Vercel 部署用的静态快照（site/）
#
# 快照里放什么：
#   HTML 外壳 + assets/ —— 内容稳定，改版才会动，适合放 CDN 边缘缓存。
#
# 快照里刻意不放什么：
#   articles/ articles.json data/ —— 机器人随时在更新，
#     放快照就意味着 Vercel 上要等重新构建才能看到新文章。
#     这三个走 vercel.json 里的 rewrites，实时转发源站。
#   downloads/ —— 必须走源站，Nginx 的付费墙（白名单）才能生效。
#     放进快照的话付费文件能被直接下载，绕过会员校验。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/site"

rm -rf "$OUT"
mkdir -p "$OUT"

# HTML 外壳
cp "$ROOT"/*.html "$OUT"/

# 静态资源
cp -r "$ROOT/assets" "$OUT"/

# robots / sitemap
for f in robots.txt sitemap.xml; do
  [ -f "$ROOT/$f" ] && cp "$ROOT/$f" "$OUT"/
done

echo "✅ Vercel 静态快照已生成：$OUT"
ls -1 "$OUT"
