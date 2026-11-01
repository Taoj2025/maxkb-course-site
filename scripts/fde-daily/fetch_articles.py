#!/usr/bin/env python3
"""
FDE（前端部署开发工程师）每日文章抓取脚本
数据源：RSSHub 公开源 + 多个 RSS 兜底
作者：小 Q 为小陶老师定制 · 2026-07-27 修复版
"""
import json
import os
import re
import sys
import requests
import feedparser
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

WORK_DIR = Path(os.environ.get("WORK_DIR", "/root/.openclaw/workspace/projects/maxkb-course-site"))
OUT_DIR = WORK_DIR / "fde-candidates"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 词表和匹配规则统一放在 relevance.py，审核阶段用的是同一份
sys.path.insert(0, str(Path(__file__).resolve().parent))
from relevance import is_relevant, count_keywords, match_keywords

# RSSHub 镜像。rsshub.app 官方实例在境内经常连不上（实测 12 秒超时），
# rssforever 这个镜像稳定，用它兜住原来那些 RSSHub 路由。
RSSHUB = "https://rsshub.rssforever.com"

# 各数据源的 RSS 路由。
#
# 这里的每个源都在生产服务器（119.91.234.159，境内）上实测过能连通并返回条目：
# 之前用的是 rsshub.app + 一串国内站点的自建路由，实测基本全超时，
# 整条管线一个候选都抓不到。
#
# 2026-11-02 全面重测（16 旧源 + 63 候选源，探针见下）后的调整：
#
# 【剔除】4 个实测失效的 rsshub 路由（503 / 超时，连续 4 天拖垮文章管线）：
#   - 36氪-AI / 36氪-科技 / 腾讯云-开发者 / 阮一峰-镜像
#   注：rsshub.rssforever.com 本身时好时坏，路由级失效；保留仍在工作的
#   掘金-前端 / 36氪快讯 / 少数派Matrix / OSCHINA 四条实测可用路由。
#
# 【排除】一批 DNS 被污染的域名 —— 解析到 Meta 的 IP 段（face:b00c），
#   在境内生产服务器上必然超时，web.dev / huggingface.co / v2ex.com /
#   rsshub.app / feedx.net 全部属此类，不要再往里加：
#     web.dev  → 2001:4860:4802:32::1b（应指 142.250.x）
#     rsshub.app → 2a03:2880:f136:83:face:b00c:0:25de（Meta 段）
#
# 【新增】7 个「新鲜度 + 相关性」双达标源（实测 3 日内新增 ≥12 条、
#   命中 FDE 词表 ≥5 条），这是解决「连续 4 天零新增」的主力：
#   开源中国(55%相关) / InfoQ English(53%) / The New Stack(42%) /
#   Lobsters / Stack Overflow Blog(45%) / Smashing Magazine(25%) /
#   CSS-Tricks / Prisma Blog / PlanetScale / Supabase Blog /
#   Shopify Engineering / Kubernetes Blog / AWS News / Azure Blog /
#   Node.js Blog / React Blog / OpenAI Blog / Google AI Blog /
#   Hacker News Best / Dev.to / 量子位 / 钛媒体 / 爱范儿
#
# 每个源都在生产服务器（119.91.234.159，境内）实测过能连通并返回条目。
SOURCES = [
    # ── 直连源 · 国内技术媒体（最稳，优先）──
    ("https://www.oschina.net/news/rss", "开源中国"),
    ("https://juejin.cn/rss", "掘金"),
    ("https://www.infoq.cn/feed", "InfoQ"),
    ("https://www.qbitai.com/feed", "量子位"),
    ("https://www.tmtpost.com/feed", "钛媒体"),
    ("https://www.ifanr.com/feed", "爱范儿"),
    ("https://sspai.com/feed", "少数派"),
    ("https://www.solidot.org/index.rss", "Solidot"),
    ("https://www.ithome.com/rss/", "IT之家"),
    ("https://www.leiphone.com/feed", "雷峰网"),
    ("https://www.ruanyifeng.com/blog/atom.xml", "阮一峰"),

    # ── 直连源 · 国际技术媒体（补充国内源覆盖不到的前端/AI 深度内容）──
    ("https://feed.infoq.com/", "InfoQ English"),
    ("https://thenewstack.io/feed/", "The New Stack"),
    ("https://lobste.rs/rss", "Lobsters"),
    ("https://stackoverflow.blog/feed/", "Stack Overflow Blog"),
    ("https://www.smashingmagazine.com/feed/", "Smashing Magazine"),
    ("https://css-tricks.com/feed/", "CSS-Tricks"),
    ("https://dev.to/feed", "Dev.to"),
    ("https://hnrss.org/best", "Hacker News Best"),
    ("https://hnrss.org/frontpage", "Hacker News"),

    # ── 直连源 · 厂商技术博客（高频更新且强相关）──
    ("https://www.prisma.io/blog/rss.xml", "Prisma Blog"),
    ("https://planetscale.com/blog/rss.xml", "PlanetScale"),
    ("https://supabase.com/blog/rss.xml", "Supabase Blog"),
    ("https://shopify.engineering/blog.atom", "Shopify Engineering"),
    ("https://kubernetes.io/feed.xml", "Kubernetes Blog"),
    ("https://aws.amazon.com/blogs/aws/feed/", "AWS News"),
    ("https://azure.microsoft.com/en-us/blog/feed/", "Azure Blog"),
    ("https://nodejs.org/en/feed/blog.xml", "Node.js Blog"),
    ("https://react.dev/rss.xml", "React Blog"),
    ("https://openai.com/blog/rss.xml", "OpenAI Blog"),
    ("https://blog.google/technology/ai/rss/", "Google AI Blog"),
    ("https://blog.cloudflare.com/rss/", "Cloudflare"),
    ("https://github.blog/feed/", "GitHub Blog"),

    # ── RSSHub 镜像（仅保留实测仍可用的路由）──
    (f"{RSSHUB}/juejin/category/frontend", "掘金-前端"),
    (f"{RSSHUB}/36kr/newsflashes", "36氪快讯"),
    (f"{RSSHUB}/sspai/matrix", "少数派Matrix"),
    (f"{RSSHUB}/oschina/news", "OSCHINA聚合"),
]

# 单个源最多等 12 秒。feedparser 自己不设超时的时候，
# 一个连不上的源能把整条管线拖住十几分钟。
FEED_TIMEOUT = 12
# 并发抓取：原来是串行，15 个源最坏要跑好几分钟
MAX_WORKERS = 6

# 相关性门槛：未命中强相关词时，至少要命中几个普通词（见 relevance.py）
MIN_KEYWORD_HITS = 2

# 强相关词：命中任意一个即判定为 FDE 相关（技术栈主体词 / AI 主体词 / 教学词）
STRONG_KEYWORDS = [
    'AI', 'LLM', 'Agent', 'MCP', 'FDE', 'DevOps', 'Serverless',
    'MaxKB', 'Vercel', 'Netlify', 'Cloudflare', 'Copilot', 'OpenAI',
    'Anthropic', 'DeepSeek', 'RAG', 'React', 'Vue', 'Next.js', 'Astro',
    'Svelte', 'Tailwind', 'TypeScript', 'Node.js', 'Kubernetes', 'Docker',
    'Supabase', 'Prisma', 'Shopify', 'FastAPI', 'GraphQL', 'Postgres',
    'PostgreSQL', 'Vite', 'Deno', 'Bun', 'Hono', 'Terraform',
    # 中文
    '前端', '部署', '智能体', '大模型', '边缘计算', '全栈', '工程化',
    '容器化', '开源', '教学', '源码',
]

# 噪声标题：版本发布日志 / 周刊 / 勘误等，对教学无价值
NOISE_TITLE_RE = re.compile(
    r'\((?:LTS|Current)\)'    r'|^\s*v?\d+\.\d+(\.\d+)?\s*\$'    r'|周刊|第\s*\d+\s*期'    r'|勘误|changelog|release notes'    r'|\bv\d+\.\d+(\.\d+)?\b'    r'|\b\d+\.\d+\.\d+\s*\('    r'|React Conf \d{4} Recap'    r'|\bKubernetes v\d'    , re.I,
)


def matches_keywords(title: str) -> bool:
    """检查标题是否相关（词表和匹配规则见 relevance.py）

    2026-11-02 修正判据。原实现是「命中 ≥N 个词」，问题在于纯计数
    区分不了两种情况：
      · 「Node.js 22.23.3 (LTS)」→ 只命中 'Node.js'，是版本日志，无价值
      · 「React Labs: View Transitions, Activity」→ 只命中 'React'，是真内容
    所以改成加权判据：命中任一强相关词即通过，否则需命中 ≥2 个普通词；
    同时用独立正则排除版本发布日志 / 周刊这类噪声标题。
    """
    if not title:
        return False
    if NOISE_TITLE_RE.search(title):
        return False
    hits = match_keywords(title)
    if not hits:
        return False
    # 命中强相关词 → 直接通过（不论数量）
    if any(kw in hits for kw in STRONG_KEYWORDS):
        return True
    # 否则要求命中 ≥2 个普通相关词
    return len(hits) >= MIN_KEYWORD_HITS


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
