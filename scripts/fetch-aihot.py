#!/usr/bin/env python3
"""
AIHOT 实时热点抓取 —— 刷新 latest.html 的数据源

数据源：https://aihot.virxact.com/feed.xml （AIHOT 精选 50 条 · TTL 30 分钟）

输出（写入 SITE_DIR 下）：
  data/aihot.json      全部热点      —— latest.html 读这个
  data/aihot-fde.json  FDE 相关子集  —— 后端 /api/aihot?category=fde 读这个

用法：
  SITE_DIR=/var/www/maxkb-course-site python3 scripts/fetch-aihot.py

设计要点：
  - 抓取失败时**不覆盖**已有数据（旧数据继续可用），以免一次网络抖动把页面打空
  - 只取最新 MAX_ITEMS 条，跳过「【AIHOT 通知】」这类公告
  - summary 保留源站的「🔗 阅读原文 via …」尾巴，与历史数据格式一致
  - FDE 子集按关键词筛选，关键词表见 FDE_KEYWORDS
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("❌ 缺少 requests：pip install requests")

# ── 配置 ──────────────────────────────────────────────────────────────
FEED_URL = "https://aihot.virxact.com/feed.xml"
SITE_DIR = Path(os.environ.get("SITE_DIR", Path(__file__).resolve().parent.parent))
MAX_ITEMS = 50
REQUEST_TIMEOUT = 30
UA = "Mozilla/5.0 (compatible; MaxKB-FDE-Bot/1.0; +https://taotaoedu.ltd)"

# FDE（前端部署开发工程师）相关性关键词
# 命中标题或摘要即视为 FDE 相关 —— 与 scripts/fde-daily/fetch_articles.py 的词表同源，
# 这里额外补了 AI 工程 / 模型发布 / 工具链相关的词。
FDE_KEYWORDS = [
    # 前端部署工程
    "FDE", "前端部署", "前端开发工程师", "前端工程化", "前端架构", "前端自动化",
    "AI前端", "LLM前端", "前端AI", "智能前端", "CI/CD", "部署", "工程化",
    # 平台 / 运行时
    "Vercel", "Netlify", "Cloudflare", "Workers", "Edge", "Next.js", "Astro", "Hono",
    "Serverless", "容器", "Kubernetes", "Docker", "边缘计算", "边缘运行时",
    # AI 工程 / 工具链
    "MCP", "AI Agent", "智能体", "Agent", "Cursor", "Copilot", "Claude Code",
    "Codex", "上下文工程", "Context Engineering", "Prompt", "提示词", "RAG",
    "检索增强", "工作流", "Workflow", "微调", "推理模型", "推理引擎",
    # 模型发布（开发者直接相关）
    "开源模型", "开放权重", "上下文窗口", "token", "推理成本", "推理速度",
    "评测基准", "评测", "Hugging Face", "推理框架", "量化", "蒸馏",
]


def log(msg):
    print(f"[fetch-aihot] {msg}", flush=True)


def strip_html(raw: str) -> str:
    """把 RSS 的 HTML 描述压成一行纯文本（段落之间用空格连接）"""
    if not raw:
        return ""
    text = re.sub(r"<\s*br\s*/?\s*>", " ", raw, flags=re.I)
    text = re.sub(r"<\s*/\s*p\s*>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_feed(xml: str) -> list:
    """解析 RSS → 规范化条目列表"""
    try:
        import feedparser
        parsed = feedparser.parse(xml)
        entries = parsed.entries
    except ImportError:
        # 没有 feedparser 时的极简兜底解析
        entries = []
        for block in re.findall(r"<item>(.*?)</item>", xml, re.S):
            def grab(tag):
                m = re.search(rf"<{tag}[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{tag}>", block, re.S)
                return m.group(1).strip() if m else ""
            entries.append({
                "title": grab("title"),
                "link": grab("link"),
                "summary": grab("description"),
                "author": grab("author"),
                "category": grab("category"),
                "published": grab("pubDate"),
            })

    items = []
    for entry in entries:
        title = (entry.get("title") or "").strip()
        if not title:
            continue
        if title.startswith("【AIHOT 通知】"):
            log(f"跳过公告：{title[:40]}")
            continue

        link = entry.get("link") or ""
        summary = strip_html(entry.get("summary") or entry.get("description") or "")

        # 日期：优先用 published_parsed，退化到字符串解析
        pub_date = ""
        pp = entry.get("published_parsed") or entry.get("updated_parsed")
        if pp:
            pub_date = datetime(*pp[:6]).strftime("%Y-%m-%d")
        else:
            raw_date = entry.get("published") or entry.get("updated") or ""
            m = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw_date)
            if m:
                pub_date = m.group(0)

        author = (entry.get("author") or "").strip()
        category = (entry.get("category") or "").strip()
        if not category:
            tags = entry.get("tags") or []
            category = (tags[0].get("term") if tags else "") or "行业动态"

        items.append({
            "title": title,
            "link": link,
            "summary": summary,
            "pub_date": pub_date,
            "author": author,
            "category": category,
        })
    return items


def is_fde(item: dict) -> bool:
    blob = f"{item['title']} {item['summary']}".lower()
    return any(kw.lower() in blob for kw in FDE_KEYWORDS)


def write_json(path: Path, source: str, items: list) -> None:
    payload = {
        "source": source,
        "updated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "total": len(items),
        "items": items,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    log(f"抓取 {FEED_URL}")
    try:
        resp = requests.get(FEED_URL, timeout=REQUEST_TIMEOUT, headers={"User-Agent": UA})
        resp.raise_for_status()
    except Exception as e:
        log(f"❌ 抓取失败：{str(e)[:120]}")
        log("   保留现有数据，不做覆盖")
        return 1

    items = parse_feed(resp.text)
    if len(items) < 5:
        log(f"❌ 只解析到 {len(items)} 条，判定为异常，保留现有数据")
        return 1

    items = items[:MAX_ITEMS]
    fde_items = [i for i in items if is_fde(i)]

    write_json(SITE_DIR / "data" / "aihot.json", "aihot.virxact.com RSS", items)
    write_json(SITE_DIR / "data" / "aihot-fde.json", "aihot.virxact.com (FDE 相关筛选)", fde_items)

    newest = items[0]["pub_date"] if items else "?"
    log(f"✅ 全部 {len(items)} 条（FDE {len(fde_items)} 条）· 最新日期 {newest}")
    log(f"   {SITE_DIR / 'data' / 'aihot.json'}")
    log(f"   {SITE_DIR / 'data' / 'aihot-fde.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
