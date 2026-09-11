#!/usr/bin/env bash
# 创建 v2.0.0 release · 需要 fine-grained PAT
# 用法：把下方 YOUR_TOKEN 替换为你的 token，然后 bash create-release.sh
# Token 生成：https://github.com/settings/personal-access-tokens/new

set -e
YOUR_TOKEN="ghp_把你的token粘贴到这里替换"

curl -sS -X POST \
  -H "Authorization: Bearer $YOUR_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/Taoj2025/maxkb-course-site/releases \
  --data-binary @backend/RELEASE-NOTES-v2.0.0.json | head -30