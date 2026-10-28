#!/usr/bin/env python3
"""
FDE 文章 · AI 自动审核 + 自动发布

审核通过后：
  1. 写 articles/<id>-<slug>.md
  2. 追加条目到 articles.json（category='最新动态'，latest.html 只显示这一类）
  3. 调用 scripts/publish-site.sh 提交并推送到 GitHub

路径全部可用环境变量覆盖：
  SITE_DIR  站点根目录（默认：脚本所在仓库根）
  WORK_DIR  中间产物目录（默认：openclaw 工作区，保持历史兼容）
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SITE_DIR = Path(os.environ.get("SITE_DIR", Path(__file__).resolve().parent.parent.parent))
WORK_DIR = Path(os.environ.get(
    "WORK_DIR", "/root/.openclaw/workspace/projects/maxkb-course-site"))
PENDING_DIR = WORK_DIR / "fde-pending"
ARTICLES_DIR = SITE_DIR / "articles"
ARTICLES_JSON = SITE_DIR / "articles.json"
PUBLISH_SCRIPT = SITE_DIR / "scripts" / "publish-site.sh"

API_KEY = os.environ.get('MINIMAX_API_KEY', '')

BAD_KEYWORDS = ['博彩', '赌博', '色情', '广告', '营销', '标题党']

# latest.html 的标签配色（见 latest.html 的 tagColors）
TAG_COLORS = ['purple', 'blue', 'green', 'orange', 'red']

# 自动生成条目的默认标签
DEFAULT_TAGS = ['FDE', 'AI 资讯', '前端部署']


def log(msg):
    print(f"[publish] {msg}", flush=True)


def ai_review(article):
    """AI 自动审核"""
    title = article.get('title', '')
    content = article.get('content', '')

    # 1. 基础过滤
    for bad in BAD_KEYWORDS:
        if bad in title or bad in content[:500]:
            return False, f"包含敏感词：{bad}"

    if len(title) < 8 or len(title) > 100:
        return False, f"标题长度异常：{len(title)} 字符"

    if len(content) < 200:
        return False, f"内容过短：{len(content)} 字符"

    # 2. AI 质量评分（仅当 API 可用）
    if API_KEY:
        try:
            prompt = f"""请评分（0-5）以下 FDE 文章质量：
标题：{title}
内容前 300 字：{content[:300]}

评分标准：
- 5 = 优质教学文章 · 有具体技术方案
- 4 = 良好资讯 · 有实用价值
- 3 = 一般 · 信息完整但价值有限
- 2 = 偏题或重复
- 1 = 低质或内容过少

仅回复一个数字（0-5）。"""
            import requests
            resp = requests.post(
                'https://api.minimax.chat/v1/text/chatcompletion_v2',
                headers={'Authorization': f'Bearer {API_KEY}'},
                json={'model': 'MiniMax-Text-01',
                      'messages': [{'role': 'user', 'content': prompt}],
                      'temperature': 0.3},
                timeout=15
            )
            score_text = resp.json()['choices'][0]['message']['content'].strip()
            score = float(re.search(r'\d+\.?\d*', score_text).group())
            if score < 3.0:
                return False, f"AI 评分过低：{score}"
            return True, f"AI 评分：{score}"
        except Exception:
            pass  # AI 失败时降级为基础规则

    # 3. 兜底：基于关键词相关性
    score = sum(1 for kw in ['FDE', '前端', 'AI', 'LLM', '工程化', '部署', '开发',
                             'MaxKB', 'Vercel', '教学'] if kw in (title + content[:500]))
    if score < 2:
        return False, f"相关性低：命中 {score} 个关键词"
    return True, f"关键词命中：{score}"


def make_slug(title: str) -> str:
    slug = re.sub(r'[^\w\s-]', '', title)[:30].strip().replace(' ', '-').lower()
    return slug or 'article'


def next_article_id(articles_data: list) -> int:
    ids = [a.get('id') for a in articles_data if isinstance(a.get('id'), int)]
    return (max(ids) + 1) if ids else 13312


def publish_article(article: dict, article_id: int, index: int) -> tuple:
    """写 markdown + 返回 articles.json 条目"""
    slug = f"{article_id}-{make_slug(article['title'])}"
    filename = f"{slug}.md"
    filepath = ARTICLES_DIR / filename
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime('%Y-%m-%d')
    content = article['content']

    md_content = f"""---
title: "{article['title']}"
source: "{article['source']}"
source_url: "{article['url']}"
date: "{date_str}"
auto: true
---

{content}

---

*本文由小Q自动抓取 + AI 重写 · 来源：[{article['source']}]({article['url']})*
"""
    filepath.write_text(md_content, encoding='utf-8')

    entry = {
        'id': article_id,
        'title': article['title'],
        'slug': slug,
        'summary': re.sub(r'\s+', ' ', content)[:150].strip(),
        'category': '最新动态',          # latest.html 只渲染这一类
        'tags': DEFAULT_TAGS,
        'color': TAG_COLORS[index % len(TAG_COLORS)],
        'date': date_str,
        'author': '小Q',
        'source': f"AI 重写 · {article['source']}",
        'file': filename,
        'estimated_read_time': f"{max(1, round(len(content) / 500))} 分钟",
    }
    return filename, entry


def push_to_git(message: str) -> bool:
    """调用 publish-site.sh 提交并推送（SSH，无需 GitHub token）"""
    if not PUBLISH_SCRIPT.exists():
        log(f"❌ 找不到发布脚本：{PUBLISH_SCRIPT}")
        return False
    env = dict(os.environ, SITE_DIR=str(SITE_DIR))
    proc = subprocess.run(
        ['bash', str(PUBLISH_SCRIPT), message],
        env=env, capture_output=True, text=True,
    )
    for line in (proc.stdout + proc.stderr).splitlines():
        log(line)
    return proc.returncode == 0


def main():
    log("=" * 50)
    log(f"🤖 AI 自动审核 + 自动发布 · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"   SITE_DIR = {SITE_DIR}")
    log("=" * 50)

    pending_files = sorted(PENDING_DIR.glob('pending_*.json'), reverse=True)
    if not pending_files:
        log("❌ 无待审核内容，请先运行 rewrite_articles.py")
        return

    with open(pending_files[0], 'r', encoding='utf-8') as f:
        articles = json.load(f)

    log(f"📋 待审 {len(articles)} 篇")

    passed, rejected = [], []
    for i, art in enumerate(articles, 1):
        ok, reason = ai_review(art)
        if ok:
            log(f"  ✅ [{i}] 通过 · {reason} · {art['title'][:30]}")
            passed.append(art)
        else:
            log(f"  ❌ [{i}] 拒绝 · {reason} · {art['title'][:30]}")
            rejected.append(art)

    log(f"📊 通过 {len(passed)} 篇 / 拒绝 {len(rejected)} 篇")
    if not passed:
        return

    # ── 写文件 + 更新 articles.json ──
    if ARTICLES_JSON.exists():
        with open(ARTICLES_JSON, 'r', encoding='utf-8') as f:
            articles_data = json.load(f)
    else:
        articles_data = []

    existing_titles = {a.get('title') for a in articles_data}
    new_id = next_article_id(articles_data)
    published = 0

    for idx, art in enumerate(passed):
        if art['title'] in existing_titles:
            log(f"  ⏭ 跳过重复：{art['title'][:30]}")
            continue
        filename, entry = publish_article(art, new_id, idx)
        articles_data.append(entry)
        log(f"  📝 {filename} → id={new_id}")
        existing_titles.add(art['title'])
        new_id += 1
        published += 1

    if published == 0:
        log("没有新文章，跳过发布")
        return

    with open(ARTICLES_JSON, 'w', encoding='utf-8') as f:
        json.dump(articles_data, f, ensure_ascii=False, indent=2)
    log(f"  📋 articles.json 已更新（{len(articles_data)} 条）")

    # ── 推送到 GitHub ──
    ok = push_to_git(f"auto: FDE 每日文章 · {published} 篇 · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if ok:
        log("✅ 发布完成")
    else:
        log("❌ 推送失败，文章已写入本地，待下次重试")
        sys.exit(1)


if __name__ == '__main__':
    main()
