#!/usr/bin/env python3
"""
FDE（前端部署开发工程师）每日文章抓取脚本
数据源：RSSHub 公开源 + 多个 RSS 兜底
作者：小 Q 为小陶老师定制 · 2026-07-27 修复版
"""
import json
import os
import re
import requests
import feedparser
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

WORK_DIR = Path(os.environ.get("WORK_DIR", "/root/.openclaw/workspace/projects/maxkb-course-site"))
OUT_DIR = WORK_DIR / "fde-candidates"
OUT_DIR.mkdir(parents=True, exist_ok=True)

KEYWORDS = [
    'FDE', '前端部署', '前端开发工程师', 'AI前端', 'LLM前端',
    '前端AI', '智能前端', '前端工程化', 'Vercel', 'Netlify',
    '前端自动化', 'CI/CD前端', 'Edge', 'MCP', 'AI Agent',
    'Cursor', 'Copilot', 'Astro', 'Hono', 'Next.js',
    'Cloudflare', 'Workers', '工程化', '部署', '前端架构'
]

# RSSHub 镜像。rsshub.app 官方实例在境内经常连不上（实测 12 秒超时），
# rssforever 这个镜像稳定，用它兜住原来那些 RSSHub 路由。
RSSHUB = "https://rsshub.rssforever.com"

# 各数据源的 RSS 路由。
#
# 这里的每个源都在生产服务器（119.91.234.159，境内）上实测过能连通并返回条目：
# 之前用的是 rsshub.app + 一串国内站点的自建路由，实测基本全超时，
# 整条管线一个候选都抓不到。
SOURCES = [
    # ── 直连源（最稳，优先）──
    ("https://www.ruanyifeng.com/blog/atom.xml", "阮一峰"),
    ("https://juejin.cn/rss", "掘金"),
    ("https://www.infoq.cn/feed", "InfoQ"),
    ("https://sspai.com/feed", "少数派"),
    ("https://www.solidot.org/index.rss", "Solidot"),
    ("https://www.ithome.com/rss/", "IT之家"),
    ("https://www.leiphone.com/feed", "雷峰网"),
    ("https://blog.cloudflare.com/rss/", "Cloudflare"),
    ("https://github.blog/feed/", "GitHub Blog"),
    ("https://hnrss.org/frontpage", "Hacker News"),

    # ── RSSHub 镜像（补充国内聚合源）──
    (f"{RSSHUB}/36kr/information/AI", "36氪-AI"),
    (f"{RSSHUB}/36kr/information/technology", "36氪-科技"),
    (f"{RSSHUB}/juejin/category/frontend", "掘金-前端"),
    (f"{RSSHUB}/juejin/category/ai", "掘金-AI"),
    (f"{RSSHUB}/cloud.tencent/developer", "腾讯云-开发者"),
    (f"{RSSHUB}/ruanyifeng/blog", "阮一峰-镜像"),
]

# 单个源最多等 12 秒。feedparser 自己不设超时的时候，
# 一个连不上的源能把整条管线拖住十几分钟。
FEED_TIMEOUT = 12
# 并发抓取：原来是串行，15 个源最坏要跑好几分钟
MAX_WORKERS = 6


def matches_keywords(title: str) -> bool:
    """检查标题是否包含关键词"""
    return any(kw.lower() in title.lower() for kw in KEYWORDS)


def fetch_one_rss(url: str, source_name: str, max_items: int = 15):
    """抓取单个 RSS 源"""
    results = []
    try:
        # 自己用 requests 抓再交给 feedparser 解析，
        # 这样超时可控（feedparser 自己不设 socket 超时，能把进程挂住）
        resp = requests.get(
            url,
            timeout=FEED_TIMEOUT,
            headers={'User-Agent': 'Mozilla/5.0 (FDE-Bot/1.0)'},
        )
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        if not feed.entries:
            print(f"    ⚠ {source_name}: 无内容")
            return results
        for entry in feed.entries[:max_items]:
            # 标题同样要清 HTML —— 它会一路写进 articles.json / .md，
            # 最后被 latest.html、article.html 直接渲染出来。
            title = re.sub(r'<[^>]+>', '', entry.get('title', '')).strip()
            if not title:
                continue
            if not matches_keywords(title):
                continue
            link = entry.get('link', '')
            # Atom 源（阮一峰等）的 link 是 dict，取 href
            if isinstance(link, dict):
                link = link.get('href', '')
            summary = entry.get('summary', '') or entry.get('description', '')
            # 清理 HTML
            summary = re.sub(r'<[^>]+>', '', summary)[:200]
            published = entry.get('published', '') or entry.get('updated', '')
            results.append({
                'title': title,
                'source': source_name,
                'url': link,
                'summary': summary,
                'published': published,
                'fetched_at': datetime.now().isoformat()
            })
    except Exception as e:
        print(f"    ❌ {source_name}: {str(e)[:80]}")
    return results


def main():
    print("=" * 60)
    print(f"📡 FDE 文章抓取 · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_results = []

    print(f"【并发扫描 {len(SOURCES)} 个数据源，超时 {FEED_TIMEOUT}s】")
    # 并发抓：一个源卡住不影响别的源，整体耗时取决于最慢的那个而不是总和
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(fetch_one_rss, url, name): name for url, name in SOURCES}
        for fut in as_completed(futures):
            name = futures[fut]
            try:
                items = fut.result()
            except Exception as e:
                print(f"  ❌ {name}: {str(e)[:60]}")
                continue
            if items:
                print(f"  ✅ {name}: {len(items)} 篇")
                all_results.extend(items)
            else:
                print(f"  · {name}: 0")

    # 去重（按标题）
    seen = set()
    unique = []
    for r in all_results:
        if r['title'] not in seen:
            seen.add(r['title'])
            unique.append(r)

    # 按发布时间倒序
    unique.sort(key=lambda x: x.get('published', ''), reverse=True)

    # 取前 20 篇
    final = unique[:20]

    print(f"\n✅ 共抓取 {len(final)} 篇不重复 FDE 文章")

    # 输出
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    output_file = OUT_DIR / f"candidates_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    print(f"📁 已保存到: {output_file}")

    # 显示前 5 篇预览
    if final:
        print(f"\n📋 预览（前 5 篇）：")
        for i, a in enumerate(final[:5], 1):
            print(f"  {i}. [{a['source']}] {a['title'][:60]}")

    return final


if __name__ == '__main__':
    main()