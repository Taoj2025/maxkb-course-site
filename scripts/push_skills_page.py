#!/usr/bin/env python3
"""独立推送 fde-skills.html + sitemap.xml + index.html 到 GitHub"""
import os
import sys
import base64
import requests
from pathlib import Path

REPO = "Taoj2025/maxkb-course-site"
PUSH_TOKEN = os.environ.get("GITHUB_PAT_TOKEN", os.environ.get("PUSH_TOKEN", ""))

if not PUSH_TOKEN:
    print("❌ 缺少 GITHUB_PAT_TOKEN 环境变量")
    sys.exit(1)

def push(filepath, message):
    """推送到 GitHub"""
    abs_path = Path(f"/root/.openclaw/workspace/projects/maxkb-course-site/site/{filepath}")
    if not abs_path.exists():
        print(f"❌ 文件不存在: {abs_path}")
        return 0
    content_b64 = base64.b64encode(abs_path.read_bytes()).decode()
    # 1. 拿 SHA
    sha_resp = requests.get(
        f"https://api.github.com/repos/{REPO}/contents/{filepath}",
        headers={'Authorization': f'token {PUSH_TOKEN}', 'Accept': 'application/vnd.github.v3+json'},
        timeout=10
    )
    sha = sha_resp.json().get('sha', '') if sha_resp.status_code == 200 else ''
    # 2. 推送
    data = {'message': message, 'content': content_b64, 'branch': 'main'}
    if sha:
        data['sha'] = sha
    resp = requests.put(
        f"https://api.github.com/repos/{REPO}/contents/{filepath}",
        headers={'Authorization': f'token {PUSH_TOKEN}', 'Content-Type': 'application/json'},
        json=data, timeout=15
    )
    if resp.status_code in (200, 201):
        print(f"✅ {filepath} → HTTP {resp.status_code}")
        return resp.status_code
    else:
        print(f"❌ {filepath} → HTTP {resp.status_code} · {resp.text[:200]}")
        return resp.status_code

if __name__ == "__main__":
    push('fde-skills.html', 'feat: 新增 FDE 技能图谱与知识要求展示页 (fde-skills.html)')
    push('sitemap.xml', 'chore: sitemap 加入 fde-skills.html')
    push('index.html', 'feat: 顶部导航加入「⚡ 技能图谱」入口')