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
import hashlib
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 相关性词表和匹配规则（和抓取阶段共用同一份）
sys.path.insert(0, str(Path(__file__).resolve().parent))
from relevance import count_keywords

SITE_DIR = Path(os.environ.get("SITE_DIR", Path(__file__).resolve().parent.parent.parent))
WORK_DIR = Path(os.environ.get(
    "WORK_DIR", "/root/.openclaw/workspace/projects/maxkb-course-site"))
PENDING_DIR = WORK_DIR / "fde-pending"
ARTICLES_DIR = SITE_DIR / "articles"
ARTICLES_JSON = SITE_DIR / "articles.json"
PUBLISH_SCRIPT = SITE_DIR / "scripts" / "publish-site.sh"

API_KEY = os.environ.get('MINIMAX_API_KEY', '')
API_BASE = os.environ.get('MINIMAX_API_BASE', 'https://api.minimaxi.com')
# AI 不可用时是否允许发布「机器摘要」文章（RSS 原文摘要，不经 AI 改写）。
# 关着 = AI 不通就一天不发；开着 = 站点照样每天有更新，但文章会明确标注来源。
ALLOW_NO_AI = os.environ.get('PUBLISH_WITHOUT_AI', '0') == '1'

BAD_KEYWORDS = ['博彩', '赌博', '色情', '广告', '营销', '标题党']

# latest.html 的标签配色（见 latest.html 的 tagColors）
TAG_COLORS = ['purple', 'blue', 'green', 'orange', 'red']

# 自动生成条目的默认标签
DEFAULT_TAGS = ['FDE', 'AI 资讯', '前端部署']

# 机器摘要模式（没有 AI 质量评分）要求的相关词命中数下限
MACHINE_MIN_HITS = 2


def log(msg):
    print(f"[publish] {msg}", flush=True)


def keyword_review(title, content):
    """不依赖 AI 的相关性把关：算命中了几个不同的相关词。

    词表和匹配规则统一放在 relevance.py，和抓取阶段用的是同一份 ——
    以前两边各写一套，审核用的词表更窄，抓取放进来的一堆文章被全部否掉。
    """
    return count_keywords(title + ' ' + content[:500])


def ai_review(article):
    """AI 自动审核"""
    title = article.get('title', '')
    content = article.get('content', '')
    machine = bool(article.get('machine_summary'))

    # 1. 基础过滤
    for bad in BAD_KEYWORDS:
        if bad in title or bad in content[:500]:
            return False, f"包含敏感词：{bad}"

    if len(title) < 8 or len(title) > 100:
        return False, f"标题长度异常：{len(title)} 字符"

    # 机器摘要模式下正文就是 RSS 摘要，没有 AI 扩写，长度门槛放低一点
    min_len = 80 if machine else 200
    if len(content) < min_len:
        return False, f"内容过短：{len(content)} 字符"

    # 2. AI 质量评分
    #
    # AI 调不通时不能像以前那样静默降级成关键词规则 —— 降级放行的后果很严重：
    # 重写环节失败时产出的占位文本照样能命中几个关键词，
    # 然后被当成正常文章发到线上。现在是「失败关闭」。
    #
    # 例外：显式开启 PUBLISH_WITHOUT_AI=1 时，允许走机器摘要模式，
    # 但门槛更严（关键词命中数要求更高），并且文章会被明确标注来源。
    if not API_KEY:
        if ALLOW_NO_AI and machine:
            return machine_review(title, content)
        return False, "未配置 MINIMAX_API_KEY，无法审核（本轮不发布）"

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
            f'{API_BASE}/v1/text/chatcompletion_v2',
            headers={'Authorization': f'Bearer {API_KEY}'},
            json={'model': 'MiniMax-Text-01',
                  'messages': [{'role': 'user', 'content': prompt}],
                  'temperature': 0.3},
            timeout=15
        )
        data = resp.json()
        # MiniMax 的业务错误不走 HTTP 状态码：HTTP 200 + base_resp.status_code != 0
        base = data.get('base_resp') or {}
        code = base.get('status_code')
        if code not in (0, None):
            raise RuntimeError(base.get('status_msg') or f'API 返回 status_code={code}')
        score_text = data['choices'][0]['message']['content'].strip()
        score = float(re.search(r'\d+\.?\d*', score_text).group())
        if score < 3.0:
            return False, f"AI 评分过低：{score}"
        return True, f"AI 评分：{score}"
    except Exception as e:
        if ALLOW_NO_AI and machine:
            log(f"⚠️ AI 审核不可用（{e}），改走机器摘要模式")
            return machine_review(title, content)
        return False, f"AI 审核不可用（{e}），本轮不发布"


def machine_review(title, content):
    """机器摘要模式的把关：没有 AI 质量评分，只能靠相关性门槛"""
    score = keyword_review(title, content)
    if score < MACHINE_MIN_HITS:
        return False, f"相关性不足：仅命中 {score} 个相关词（机器模式要求 ≥{MACHINE_MIN_HITS}）"
    return True, f"机器摘要 · 命中 {score} 个相关词"


def make_slug(title: str) -> str:
    """生成 ASCII slug。

    中文标题直接拿来做 slug 会得到一串要 URL 编码的中文地址，
    这里先留下能用的 ASCII 部分，不够就用标题的短哈希补上。
    """
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', title).strip('-').lower()
    if len(slug) < 3:
        slug = 'post-' + hashlib.md5(title.encode('utf-8')).hexdigest()[:8]
    return slug[:40].strip('-')


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
    machine = bool(article.get('machine_summary'))

    # 机器摘要模式的内容没有经过 AI 改写，页脚和来源必须如实标注，
    # 不能让读者以为这是「小陶老师」写的深度文章。
    byline = ('*本文由小Q自动抓取 · 机器摘要（未经 AI 改写） · 来源：'
              f"[{article['source']}]({article['url']})*") if machine else (
        f"*本文由小Q自动抓取 + AI 重写 · 来源：[{article['source']}]({article['url']})*")

    md_content = f"""---
title: "{article['title']}"
source: "{article['source']}"
source_url: "{article['url']}"
date: "{date_str}"
auto: true
machine_summary: {str(machine).lower()}
---

{content}

---

{byline}
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
        'author': '小Q（机器摘要）' if machine else '小Q',
        'source': f"机器摘要 · {article['source']}" if machine else f"AI 重写 · {article['source']}",
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

    if not API_KEY:
        # 没有 key 就没法做 AI 质量审核。
        # 开了机器摘要模式就继续走（门槛更严），否则本轮不发。
        if ALLOW_NO_AI:
            log("⚠️ 未配置 MINIMAX_API_KEY，本轮走机器摘要模式（PUBLISH_WITHOUT_AI=1）")
        else:
            log("❌ 未配置 MINIMAX_API_KEY，本轮不发布任何文章")
            log("   （检查 /root/.secrets/minimax.env 是否存在且 cron 有没有 source 它）")
            sys.exit(1)

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
