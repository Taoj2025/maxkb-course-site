#!/usr/bin/env python3
"""推送 FDE 招聘数据 + 5 篇 FDE 文章 + sitemap 升级到 GitHub"""
import os
import sys
import base64
import json
import requests
from pathlib import Path

REPO = "Taoj2025/maxkb-course-site"
PUSH_TOKEN = os.environ.get("GITHUB_PAT_TOKEN", os.environ.get("PUSH_TOKEN", ""))

if not PUSH_TOKEN:
    print("❌ 缺少 token")
    sys.exit(1)

def push(filepath, message):
    abs_path = Path(f"/root/.openclaw/workspace/projects/maxkb-course-site/site/{filepath}")
    if not abs_path.exists():
        print(f"❌ 文件不存在: {filepath}")
        return 0
    content_b64 = base64.b64encode(abs_path.read_bytes()).decode()
    sha_resp = requests.get(
        f"https://api.github.com/repos/{REPO}/contents/{filepath}",
        headers={'Authorization': f'token {PUSH_TOKEN}', 'Accept': 'application/vnd.github.v3+json'},
        timeout=10
    )
    sha = sha_resp.json().get('sha', '') if sha_resp.status_code == 200 else ''
    data = {'message': message, 'content': content_b64, 'branch': 'main'}
    if sha:
        data['sha'] = sha
    resp = requests.put(
        f"https://api.github.com/repos/{REPO}/contents/{filepath}",
        headers={'Authorization': f'token {PUSH_TOKEN}', 'Content-Type': 'application/json'},
        json=data, timeout=15
    )
    print(f"{'✅' if resp.status_code in (200,201) else '❌'} {filepath} → HTTP {resp.status_code}")
    return resp.status_code

if __name__ == "__main__":
    push('data/fde-jobs-2026.json', 'data: FDE 招聘数据 2026 完整版（国内 20 强 + 海外 20 强 + Boss/拉勾抓取框架）')
    push('sitemap.xml', 'chore: sitemap 加入 fde-skills.html + fde-jobs-2026.json')