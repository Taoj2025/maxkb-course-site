#!/bin/bash
# Vercel 部署验证 —— 部署完跑这个
#
# 用法：bash scripts/verify-vercel-deploy.sh <你的域名>
# 例：  bash scripts/verify-vercel-deploy.sh maxkb-course-site.vercel.app
#
# 检查的是这套「CDN 代理」方案里所有容易出问题的点：
#   静态快照、动态转发、API 转发、付费墙、缓存头
set -uo pipefail

DOMAIN="${1:-}"
ORIGIN="https://taotaoedu.ltd"

if [ -z "$DOMAIN" ]; then
  echo "用法：bash scripts/verify-vercel-deploy.sh <你的域名>"
  exit 1
fi

BASE="https://${DOMAIN}"
PASS=0
FAIL=0

# check <说明> <期望> <实际>
check() {
  if [ "$2" = "$3" ]; then
    printf "  ✅ %-46s %s\n" "$1" "$3"
    PASS=$((PASS + 1))
  else
    printf "  ❌ %-46s 期望 %s，实际 %s\n" "$1" "$2" "$3"
    FAIL=$((FAIL + 1))
  fi
}

code() { curl -s -o /dev/null -w "%{http_code}" --max-time 25 "$1"; }
head_of() { curl -s --max-time 25 "$1" | head -c "${2:-60}"; }

echo "═══════════════════════════════════════════════════"
echo "Vercel 部署验证 · $BASE"
echo "═══════════════════════════════════════════════════"

echo
echo "【1】静态快照（Vercel 自己托管的 HTML 外壳）"
check "/"                        200 "$(code "$BASE/")"
check "/index.html"              200 "$(code "$BASE/index.html")"
check "/latest.html"             200 "$(code "$BASE/latest.html")"
check "/membership.html"         200 "$(code "$BASE/membership.html")"
check "/assets/css/style.css"    200 "$(code "$BASE/assets/css/style.css")"

echo
echo "【2】动态内容转发（rewrite → 源站，必须是实时最新的）"
check "/articles.json"           200 "$(code "$BASE/articles.json")"
check "/data/aihot.json"         200 "$(code "$BASE/data/aihot.json")"

# articles.json 要和源站一致 —— 不一致说明 rewrite 没生效，Vercel 在发自己的静态副本
V_COUNT=$(curl -s --max-time 25 "$BASE/articles.json" | grep -c '"id":' 2>/dev/null || echo 0)
O_COUNT=$(curl -s --max-time 25 "$ORIGIN/articles.json" | grep -c '"id":' 2>/dev/null || echo 0)
check "articles.json 条数与源站一致" "$O_COUNT" "$V_COUNT"

echo
echo "【3】API 转发（Routing Middleware → 源站）"
check "/api/health"              200 "$(code "$BASE/api/health")"
check "/api/articles"            200 "$(code "$BASE/api/articles")"
check "/api/aihot"               200 "$(code "$BASE/api/aihot")"
# 未登录访问 /api/auth/me 应该是 401（说明请求真的到了后端，而不是被静态文件糊弄）
check "/api/auth/me 未登录→401"  401 "$(code "$BASE/api/auth/me")"

# ↓ 多段路径。这一批是踩过坑的：
#   api/[...path].js 这种 catch-all 文件名在这套配置下只匹配单段，
#   /api/auth/me、/api/download/<slug> 这种多段路径会落到 Vercel 自己的 404 页，
#   函数根本不被调用 —— 登录、会员校验、付费下载全断。
#   现在由 proxy.mjs（Routing Middleware，matcher=/api/:func*）接管。
check "/api/auth/me 多段→401"   401 "$(code "$BASE/api/auth/me")"
check "/api/dl-course/chapters 多段→200" 200 "$(code "$BASE/api/dl-course/chapters")"

# 文章详情（带路径参数的多段路径）
SLUG=$(curl -s --max-time 25 "$BASE/articles.json" | grep -oE '"slug"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed -E 's/.*"([^"]+)"/\1/')
if [ -n "$SLUG" ]; then
  check "/api/articles/<slug> 多段→200" 200 "$(code "$BASE/api/articles/$SLUG")"
else
  echo "  ⚠️  没取到 slug，跳过 /api/articles/<slug>"
fi

# POST 请求体转发（登录就是 POST；body 丢了后端就认不出「错密码」）
LOGIN_CODE=$(curl -s -o /tmp/.vlogin -w "%{http_code}" --max-time 25 \
  -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -H "Origin: $BASE" \
  -d '{"email":"nobody@example.com","password":"wrong-password"}')
LOGIN_BODY=$(head -c 120 /tmp/.vlogin 2>/dev/null | tr -d '\r\n')
rm -f /tmp/.vlogin
check "POST /api/auth/login 错密码→401" 401 "$LOGIN_CODE"
case "$LOGIN_BODY" in
  *密码*|*邮箱*) echo "  ✅ 请求体完整到达后端：$LOGIN_BODY" ;;
  *) echo "  ❌ 后端没读到请求体：$LOGIN_BODY"; FAIL=$((FAIL + 1)) ;;
esac

echo
echo "【4】付费墙（downloads 必须转发到源站，让 Nginx 的白名单生效）"
check "/downloads/r_m3n4o5p6.md 免费→200" 200 "$(code "$BASE/downloads/r_m3n4o5p6.md")"
check "/downloads/images.zip 付费→404"   404 "$(code "$BASE/downloads/images.zip")"
check "/downloads/r_a1b2c3d4.docx 付费→404" 404 "$(code "$BASE/downloads/r_a1b2c3d4.docx")"

echo
echo "【5】缓存头（Vercel 边缘缓存策略）"
VENDOR_CC=$(curl -s -D - -o /dev/null --max-time 25 "$BASE/assets/js/vendor/marked.min.js" | grep -i "^cache-control" | tr -d '\r')
OWN_CC=$(curl -s -D - -o /dev/null --max-time 25 "$BASE/assets/js/script.js" | grep -i "^cache-control" | tr -d '\r')
echo "  vendor js  : ${VENDOR_CC:-（无）}"
echo "  自有 js    : ${OWN_CC:-（无）}"

echo
echo "【6】前端 API 基址（config.js 里的 API_BASE 必须是空的 = 同源）"
BASE_VAL=$(head_of "$BASE/assets/js/config.js" 4000 | grep -oE "API_BASE: *'[^']*'" | head -1)
echo "  $BASE_VAL"
case "$BASE_VAL" in
  "API_BASE: ''") echo "  ✅ 同源（Vercel 上走自己的 /api 函数）"; PASS=$((PASS + 1)) ;;
  *) echo "  ❌ 不是同源，前端会绕过代理直连源站"; FAIL=$((FAIL + 1)) ;;
esac

echo
echo "═══════════════════════════════════════════════════"
echo "通过 $PASS · 失败 $FAIL"
echo "═══════════════════════════════════════════════════"
[ "$FAIL" -eq 0 ] || exit 1
