#!/usr/bin/env python3
"""
FDE（前端部署开发工程师）每日文章抓取脚本
数据源：RSSHub 公开源 + 多个 RSS 兜底
作者：小 Q 为小陶老师定制 · 2026-07-27 修复版
"""
import json
import requests
import feedparser
from datetime import datetime, timedelta
from pathlib import Path

OUT_DIR = Path('/root/.openclaw/workspace/projects/maxkb-course-site/fde-candidates')
OUT_DIR.mkdir(parents=True, exist_ok=True)

KEYWORDS = [
    'FDE', '前端部署', '前端开发工程师', 'AI前端', 'LLM前端',
    '前端AI', '智能前端', '前端工程化', 'Vercel', 'Netlify',
    '前端自动化', 'CI/CD前端', 'Edge', 'MCP', 'AI Agent',
    'Cursor', 'Copilot', 'Astro', 'Hono', 'Next.js',
    'Cloudflare', 'Workers', '工程化', '部署', '前端架构'
]

# RSSHub 公共实例（无需 API key）
RSSHUB = "https://rsshub.app"

# 各数据源的 RSSHub 路由
SOURCES = [
    # 36氪 - 前端/AI 资讯
    (f"{RSSHUB}/36kr/information/AI", "36氪-AI"),
    (f"{RSSHUB}/36kr/information/technology", "36氪-科技"),
    # InfoQ 中文
    (f"{RSSHUB}/infoq/recommend", "InfoQ-推荐"),
    (f"{RSSHUB}/infoq/topic/前端", "InfoQ-前端"),
    # 掘金 - 热门文章
    (f"{RSSHUB}/juejin/category/frontend", "掘金-前端"),
    (f"{RSSHUB}/juejin/category/ai", "掘金-AI"),
    # 腾讯云前端
    (f"{RSSHUB}/cloud.tencent/developer", "腾讯云-开发者"),
    # 知乎 - 前端话题
    (f"{RSSHUB}/zhihu/topic/19551432/top_answers", "知乎-前端话题"),
    # GitHub Trending
    ("https://mshibanami.github.io/GitHubTrendingRSS/weekly/all.xml", "GitHub-Trending"),
    # 阮一峰的网络日志
    (f"{RSSHUB}/ruanyifeng/blog", "阮一峰"),
    # 独立博客
    (f"{RSSHUB}/blog/williamfzc", "好工具分享"),
]


def matches_keywords(title: str) -> bool:
    """检查标题是否包含关键词"""
    return any(kw.lower() in title.lower() for kw in KEYWORDS)


def fetch_one_rss(url: str, source_name: str, max_items: int = 15):
    """抓取单个 RSS 源"""
    results = []
    try:
        feed = feedparser.parse(url, agent='Mozilla/5.0 (FDE-Bot/1.0)')
        if not feed.entries:
            print(f"    ⚠ {source_name}: 无内容")
            return results
        for entry in feed.entries[:max_items]:
            title = entry.get('title', '').strip()
            if not title:
                continue
            if not matches_keywords(title):
                continue
            link = entry.get('link', '')
            summary = entry.get('summary', '') or entry.get('description', '')
            # 清理 HTML
            import re
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
    print(f"📡 FDE 文章抓取（RSSHub 公共源）· {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_results = []

    print(f"【扫描 {len(SOURCES)} 个数据源】")
    for url, name in SOURCES:
        print(f"  · {name} ... ", end='', flush=True)
        items = fetch_one_rss(url, name)
        if items:
            print(f"✅ {len(items)} 篇")
            all_results.extend(items)
        else:
            print("0")

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