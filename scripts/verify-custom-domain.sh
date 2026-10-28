#!/bin/bash
# 自定义域名 → Vercel 的连通性验证
#
# 用法：在【国内服务器】上跑（国内视角才是关键）
#   bash scripts/verify-custom-domain.sh v.taotaoedu.ltd
#
# 查四件事：
#   1. 国内 DNS 解析器看到的是不是 Vercel 的真 IP（不是被污染的 Facebook IP）
#   2. TLS 握手 + HTTP 能不能通
#   3. 多段 API 路径能不能用（顺便验证 Routing Middleware 部署成功没有）
#   4. 静态快照和源站是否一致
set -uo pipefail

DOMAIN="${1:-}"
ORIGIN="https://taotaoedu.ltd"

if [ -z "$DOMAIN" ]; then
  echo "用法：bash scripts/verify-custom-domain.sh <自定义域名>"
  exit 1
fi

PASS=0
FAIL=0
check() {
  if [ "$2" = "$3" ]; then
    printf "  ✅ %-44s %s\n" "$1" "$3"
    PASS=$((PASS + 1))
  else
    printf "  ❌ %-44s 期望 %s，实际 %s\n" "$1" "$2" "$3"
    FAIL=$((FAIL + 1))
  fi
}

echo "═══════════════════════════════════════════════════"
echo "自定义域名验证 · $DOMAIN （视角：$(curl -s --max-time 10 https://api.ipify.org 2>/dev/null || echo '本机'))"
echo "═══════════════════════════════════════════════════"

echo
echo "【1】DNS 解析（国内公共解析器）"
for r in 223.5.5.5 119.29.29.29; do
  IPS=$(dig +short +time=4 +tries=1 "@$r" "$DOMAIN" A 2>/dev/null | tr '\n' ' ')
  echo "  $r → ${IPS:-（无记录）}"
  # Vercel 的 IP 段：76.76.21.x / 66.33.60.x / 64.239.x / 64.29.x / 216.198.x
  if echo "$IPS" | grep -qE '(76\.76\.21|66\.33\.60|64\.239|64\.29|216\.198)\.'; then
    echo "     ✅ 指向 Vercel 的 IP"
    PASS=$((PASS + 1))
  else
    echo "     ❌ 不是 Vercel 的 IP —— 可能是 DNS 污染，或记录还没生效"
    FAIL=$((FAIL + 1))
  fi
done

echo
echo "【2】TLS + HTTP"
CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 20 "https://$DOMAIN/" 2>/dev/null)
check "https://$DOMAIN/ → 200" 200 "$CODE"

CERT=$(echo | timeout 20 openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null \
  | openssl x509 -noout -subject -issuer 2>/dev/null | tr '\n' ' ')
echo "  证书：${CERT:-（取不到）}"
case "$CERT" in
  *"vercel"*) echo "     ✅ 是 Vercel 签发的证书"; PASS=$((PASS + 1)) ;;
  *) echo "     ⚠️  不是 Vercel 的证书（还没签发完，或指错地方了）" ;;
esac

echo
echo "【3】多段 API 路径（Routing Middleware 是否生效）"
check "/api/health"                 200 "$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "https://$DOMAIN/api/health")"
check "/api/auth/me 未登录→401"      401 "$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "https://$DOMAIN/api/auth/me")"
check "/api/dl-course/chapters→200" 200 "$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "https://$DOMAIN/api/dl-course/chapters")"
check "/api/articles/<slug>→200"     200 "$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "https://$DOMAIN/api/articles/13312-post-3f110ee3")"
check "/api/admin/stats→401"         401 "$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "https://$DOMAIN/api/admin/stats")"

echo
echo "【4】内容与源站一致（rewrite 是否生效）"
V=$(curl -s --max-time 20 "https://$DOMAIN/articles.json" | grep -c '"id":' 2>/dev/null || echo 0)
O=$(curl -s --max-time 20 "$ORIGIN/articles.json" | grep -c '"id":' 2>/dev/null || echo 0)
check "articles.json 条数与源站一致" "$O" "$V"

echo
echo "【5】付费墙仍然生效（downloads 必须回源）"
check "/downloads/r_m3n4o5p6.md 免费→200" 200 "$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "https://$DOMAIN/downloads/r_m3n4o5p6.md")"
check "/downloads/images.zip 付费→404"    404 "$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "https://$DOMAIN/downloads/images.zip")"

echo
echo "═══════════════════════════════════════════════════"
echo "通过 $PASS · 失败 $FAIL"
echo "═══════════════════════════════════════════════════"
[ "$FAIL" -eq 0 ] || exit 1
