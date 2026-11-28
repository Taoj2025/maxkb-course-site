#!/usr/bin/env python3
"""
Vercel 别名同步 —— 把 production 别名指到最新的 READY 部署
================================================================

用法（服务器 cron 调用，或手动跑）：
    python3 scripts/vercel-alias-sync.py
    python3 scripts/vercel-alias-sync.py --dry-run   # 只看，不改

================================================================
为什么需要这个脚本
================================================================

Hobby 计划的 `deployment-alias` 检查**永远不会 resolve** —— 一路挂着
`pending`，生产别名不会自己跟到新部署上（VERCEL-DEPLOY.md 坑四）。
所以每次部署完都得手动 `npm run deploy:alias`。

这个脚本把「手动」变成「自动」：服务器上每 10 分钟跑一次，
发现 Vercel 上有更新的 READY 部署，就把别名指过去。

================================================================
为什么放在服务器上跑
================================================================

- 服务器本来就在跑内容机器人（每 30 分钟推一次），顺带同步别名很自然；
- 不用在 GitHub Actions 里塞 Vercel token（那个 token 有有效期，
  放 Actions secrets 里过期了要手动换）；
- 服务器已经装了 Vercel CLI（/usr/local/bin/vercel），凭证在
  /root/.local/share/com.vercel.cli/auth.json，CLI 会自己续期。

================================================================
认证
================================================================

复用 CLI 的 auth.json（CLI 自己会 refresh，不用管过期）。
如果 CLI 没装或者 auth.json 不在，退回读环境变量 VERCEL_TOKEN。

================================================================
国内网络的坑
================================================================

api.vercel.com 直连会偶发连接超时（这台机器上表现为 connect timeout）。
所以每个请求都重试 3 次，且用 Python urllib 而不是 bash curl
（bash curl 在这台机器上还有 10~20% 概率连接重置，见记忆 curl-utf8-chinese）。
"""

import json
import os
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request

API = "https://api.vercel.com"
TEAM_ID = "team_2dTUGMzSgTA8N61C93mDosKD"
PROJECT_ID = "prj_Hr5TVLT26KxTEbhz3GV91haeMju2"

# 要管的别名：自定义域名 + 两个 .vercel.app
ALIASES = [
    "v.taotaoedu.ltd",
    "maxkb-course-site-bk10.vercel.app",
    "maxkb-course-site-bk10-tjmtaotao358-3909s-projects.vercel.app",
]

CLI_AUTH = "/root/.local/share/com.vercel.cli/auth.json"


def log(msg):
    print(msg, flush=True)


def read_token():
    """拿 Vercel token：先环境变量，再 CLI 的 auth.json（会自动续期）。"""
    tok = os.environ.get("VERCEL_TOKEN")
    if tok:
        return tok
    try:
        with open(CLI_AUTH, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        log(f"❌ 拿不到 Vercel token：{e}")
        log("   装 CLI：npm i -g vercel；或设置环境变量 VERCEL_TOKEN")
        return None

    # token 过期了就让 CLI 续一次。
    #
    # ⚠️ CLI 自己会拿 auth.json 里的 refreshToken 换新 token 并写回文件，
    #    所以调 `vercel whoami` 就能续期 —— 但它需要能连上 api.vercel.com。
    #    这台服务器在国内，直连 api.vercel.com 时通时不通（10 次里大概 3~5 次能连上），
    #    所以这里多试几次。
    if data.get("expiresAt") and data["expiresAt"] < time.time() + 300:
        log("token 已过期，尝试用 CLI 续期…")
        for _ in range(6):
            try:
                subprocess.run(
                    ["vercel", "whoami"],
                    cwd="/tmp",
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=90,
                )
            except Exception:
                pass
            try:
                with open(CLI_AUTH, encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("expiresAt", 0) > time.time() + 300:
                    log("✅ token 已续期")
                    break
            except Exception:
                pass
            time.sleep(10)

    return data.get("token")


def api(path, method="GET", body=None, token=None, retries=3):
    """调 Vercel API。返回 (status, json|str)。失败重试 3 次。"""
    url = API + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                data=data,
                method=method,
                headers={
                    "Authorization": "Bearer " + token,
                    "Content-Type": "application/json",
                    "User-Agent": "maxkb-alias-sync/1.0",
                },
            )
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
                raw = r.read().decode("utf-8", "replace")
                try:
                    return r.status, json.loads(raw)
                except Exception:
                    return r.status, raw
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            try:
                return e.code, json.loads(raw)
            except Exception:
                return e.code, raw
        except Exception as e:
            last = e
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
    return None, str(last)


def main():
    dry = "--dry-run" in sys.argv
    token = read_token()
    if not token:
        return 2

    # ── 找最新的 READY production 部署 ──
    status, data = api(
        f"/v6/deployments?projectId={PROJECT_ID}&target=production&limit=10",
        token=token,
    )
    if status != 200 or not isinstance(data, dict):
        log(f"❌ 查部署列表失败：{status} {str(data)[:120]}")
        return 1

    ready = [d for d in data.get("deployments", []) if d.get("readyState") == "READY"]
    if not ready:
        log("ℹ️ 没有 READY 的 production 部署，跳过")
        return 0
    ready.sort(key=lambda d: d.get("createdAt", 0), reverse=True)
    target = ready[0]
    did = target.get("uid")
    meta = target.get("meta") or {}
    log(f"目标部署：{did}")
    log(f"  commit : {meta.get('githubCommitSha', '?')[:7]}")
    log(f"  提交   : {(meta.get('githubCommitMessage') or '').splitlines()[0][:50]}")
    log(f"  创建于 : {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(target.get('createdAt', 0) / 1000))}")

    # ── 看看别名现在指向哪 ──
    need = []
    for alias in ALIASES:
        status, cur = api(f"/v4/aliases/{alias}?teamId={TEAM_ID}", token=token)
        cur_id = (cur.get("deployment") or {}).get("id") if isinstance(cur, dict) else None
        if cur_id == did:
            log(f"  ✅ {alias} 已指向目标部署")
        else:
            log(f"  ↪️  {alias} → {cur_id}（需要改）")
            need.append(alias)

    if not need:
        log("✅ 所有别名都已是最新，无需改动")
        return 0

    if dry:
        log(f"--dry-run：本来要改 {len(need)} 个别名")
        return 0

    bad = 0
    for alias in need:
        status, resp = api(
            f"/v2/deployments/{did}/aliases?teamId={TEAM_ID}",
            method="POST",
            body={"alias": alias},
            token=token,
        )
        if status in (200, 201):
            log(f"  ✅ 已指派 {alias}")
        else:
            log(f"  ❌ 指派 {alias} 失败：{status} {str(resp)[:120]}")
            bad += 1

    # ── 核对 ──
    log("核对：")
    for alias in ALIASES:
        status, cur = api(f"/v4/aliases/{alias}?teamId={TEAM_ID}", token=token)
        cur_id = (cur.get("deployment") or {}).get("id") if isinstance(cur, dict) else None
        ok = cur_id == did
        if not ok:
            bad += 1
        log(f"  {'✅' if ok else '❌'} {alias} → {cur_id}")

    if bad:
        log(f"❌ 有 {bad} 处没对齐")
        return 1
    log("✅ 全部别名已指向最新部署")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
