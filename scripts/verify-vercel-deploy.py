#!/usr/bin/env python3
"""
Vercel 部署验证 —— 部署完跑这个

用法：python scripts/verify-vercel-deploy.py <域名>
例：  python scripts/verify-vercel-deploy.py v.taotaoedu.ltd

检查的是这套「CDN 代理」方案里所有容易出问题的点：
  静态快照、动态转发、API 转发（多段路径）、付费墙、缓存头、部署指纹

为什么用 Python 而不是 bash curl：
  1. bash curl 在这台机器上会偶发连接重置（约 10~20% 的请求），
     表现是「实际 000」，让人误判成部署没生效 —— 2026-10-29 排查时被带偏过。
  2. 响应体里有中文，bash curl 会把 UTF-8 弄乱
     （见记忆 curl-utf8-chinese）。登录接口的报错是中文「邮箱或密码错误」，
     curl 拿到乱码就判不出「请求体有没有真的到后端」。
  所以这个脚本用 urllib，并且对每个请求重试 3 次。

每次请求都会带真实浏览器 UA —— 源站的 cors 白名单不认陌生 Origin，
所以这里既不发 Origin 头，也不依赖 CORS。
"""

import json
import re
import sys
import time
import urllib.error
import urllib.request

DOMAIN = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
ORIGIN = "https://taotaoedu.ltd"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

if not DOMAIN:
    print("用法：python scripts/verify-vercel-deploy.py <域名>")
    sys.exit(2)

BASE = "https://" + DOMAIN
PASS = 0
FAIL = 0
SKIP = 0


def fetch(url, method="GET", body=None, headers=None, retries=3, timeout=30):
    """返回 (状态码, 响应体文本, 响应头)。连不上时状态码为 None。"""
    h = dict(UA)
    if headers:
        h.update(headers)
    data = body.encode("utf-8") if body else None
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", "replace"), dict(r.headers)
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            hds = dict(e.headers)
            # 5xx 也重试：Vercel 边缘 → 国内源站这条链路偶尔会闪断
            if e.code >= 500 and attempt < retries - 1:
                last = (e.code, raw, hds)
                time.sleep(1.5 * (attempt + 1))
                continue
            return e.code, raw, hds
        except Exception as e:
            last = (None, "%s: %s" % (type(e).__name__, str(e)[:80]), {})
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
    return last


def check(name, expected, actual):
    global PASS, FAIL
    if actual == expected:
        PASS += 1
        print("  ✅ %-46s %s" % (name, actual))
    else:
        FAIL += 1
        print("  ❌ %-46s 期望 %s，实际 %s" % (name, expected, actual))


def code(path):
    st, _, _ = fetch(BASE + path)
    return st


print("=" * 51)
print("Vercel 部署验证 · %s" % BASE)
print("=" * 51)

print()
print("【1】静态快照（Vercel 自己托管的 HTML 外壳）")
for p in ["/", "/index.html", "/latest.html", "/membership.html", "/assets/css/style.css"]:
    check(p, 200, code(p))

# 部署指纹 —— 确认线上跑的是哪一次构建。
# 静态文件基本不变时，光看页面分不出新旧部署（2026-10-29 就是因为别名没跟过去，
# 页面看着一样，排查了半天）。
print()
print("【1.5】部署指纹（build-info.json）")
st, body, _ = fetch(BASE + "/build-info.json")
remote_sha = ""
try:
    remote_sha = json.loads(body).get("sha", "")
except Exception:
    pass
import subprocess
try:
    local_sha = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
    ).decode().strip()
except Exception:
    local_sha = "unknown"
if not remote_sha:
    FAIL += 1
    print("  ❌ %-46s 拿不到 build-info.json（部署可能是旧的）" % "线上 commit")
elif remote_sha == "unknown":
    FAIL += 1
    print("  ❌ %-46s 线上 sha 是 unknown —— 构建脚本没用 VERCEL_GIT_COMMIT_SHA" % "线上 commit")
elif remote_sha == local_sha:
    PASS += 1
    print("  ✅ %-46s %s" % ("线上 commit = 本地 HEAD", remote_sha))
else:
    FAIL += 1
    print("  ❌ %-46s 线上 %s，本地 %s —— 部署没更新" % ("线上 commit", remote_sha, local_sha))

print()
print("【2】动态内容转发（rewrite → 源站，必须是实时最新的）")
check("/articles.json", 200, code("/articles.json"))
check("/data/aihot.json", 200, code("/data/aihot.json"))

# articles.json 要和源站一致 —— 不一致说明 rewrite 没生效，Vercel 在发自己的静态副本
_, v_body, _ = fetch(BASE + "/articles.json")
_, o_body, _ = fetch(ORIGIN + "/articles.json")
try:
    v_count = len(json.loads(v_body))
except Exception:
    v_count = 0
try:
    o_count = len(json.loads(o_body))
except Exception:
    o_count = 0
check("articles.json 条数与源站一致", o_count, v_count)

print()
print("【3】API 转发（Routing Middleware → 源站）")
check("/api/health", 200, code("/api/health"))
check("/api/articles", 200, code("/api/articles"))
check("/api/aihot", 200, code("/api/aihot"))
check("/api/auth/me 未登录→401", 401, code("/api/auth/me"))

# ↓ 多段路径。这一批是踩过坑的：
#   Vercel 生成 api 目录路由时，文件名里的 [...] 只当「单段动态参数」，
#   api/[...path].js 的正则是 ^/api/([^/]+)$ —— 多段路径（/api/auth/me、
#   /api/download/<slug>）会落到 Vercel 自己的 404 页，函数根本不被调用，
#   登录、会员校验、付费下载全断。
#   现在由 proxy.js（Routing Middleware，matcher=/api/:func*）接管。
check("/api/auth/me 多段→401", 401, code("/api/auth/me"))
check("/api/dl-course/chapters 多段→200", 200, code("/api/dl-course/chapters"))

slug = ""
try:
    slug = json.loads(v_body)[0].get("slug", "")
except Exception:
    pass
if slug:
    check("/api/articles/<slug> 多段→200", 200, code("/api/articles/" + slug))
else:
    SKIP += 1
    print("  ⚠️  没取到 slug，跳过 /api/articles/<slug>")

# POST 请求体转发（登录就是 POST；body 丢了后端就认不出「错密码」）
# 顺带带上 Origin 头：如果转发层没把 Origin 摘掉，
# 源站的 cors 白名单会把这个请求打成 500 而不是 401。
st, body, _ = fetch(
    BASE + "/api/auth/login",
    method="POST",
    body=json.dumps({"email": "nobody@example.com", "password": "wrong-password"}),
    headers={"Content-Type": "application/json", "Origin": BASE},
)
check("POST /api/auth/login 错密码→401", 401, st)
if ("密码" in body) or ("邮箱" in body):
    PASS += 1
    print("  ✅ %-46s %s" % ("请求体完整到达后端", body[:60].replace("\n", " ")))
else:
    FAIL += 1
    print("  ❌ %-46s %s" % ("后端没读到请求体", body[:80]))

print()
print("【4】付费墙（downloads 必须转发到源站，让 Nginx 的白名单生效）")
check("/downloads/r_m3n4o5p6.md 免费→200", 200, code("/downloads/r_m3n4o5p6.md"))
check("/downloads/images.zip 付费→404", 404, code("/downloads/images.zip"))
check("/downloads/r_a1b2c3d4.docx 付费→404", 404, code("/downloads/r_a1b2c3d4.docx"))

print()
print("【5】缓存头（Vercel 边缘缓存策略）")
for p in ["/assets/js/vendor/marked.min.js", "/assets/js/script.js"]:
    _, _, h = fetch(BASE + p)
    print("  %-46s %s" % (p, h.get("Cache-Control") or h.get("cache-control") or "（无）"))

print()
print("【6】前端 API 基址（config.js 里的 API_BASE 必须是空的 = 同源）")
_, cfg, _ = fetch(BASE + "/assets/js/config.js")
api_base = ""
for line in cfg.splitlines():
    # 只认 API_BASE 这一项，别把 API_BASE_FALLBACK 和注释里的说明也捞进来
    if line.strip().startswith("API_BASE:"):
        api_base = line.strip()
        break
print("  %s" % (api_base or "（没找到 API_BASE）"))
if re.match(r"API_BASE:\s*''", api_base):
    PASS += 1
    print("  ✅ %-46s 同源（Vercel 上走自己的中间件）" % "")
else:
    FAIL += 1
    print("  ❌ %-46s 不是同源，前端会绕过代理直连源站" % "")

print()
print("=" * 51)
print("通过 %d · 失败 %d%s" % (PASS, FAIL, (" · 跳过 %d" % SKIP) if SKIP else ""))
print("=" * 51)
sys.exit(1 if FAIL else 0)
