#!/usr/bin/env python3
"""
FDE 相关性词表与匹配规则

抓取（fetch_articles.py）和审核（auto_review_and_publish.py）都要判断
「这篇文章和 FDE / 前端 / AI 是不是相关」。这两处以前各写了一份词表，
结果审核用的词表比抓取窄得多，还是不区分大小写的子串匹配 ——
抓取放进来一堆东西，审核又用另一套标准把它们全否掉。

现在统一放在这里：

  - 中文词直接子串匹配（「前端」「部署」…）
  - 英文/缩写按单词边界匹配，不能用子串 ——
    'AI' 会命中 'email'、'maintain'，'Edge' 会命中 'knowledge'

用法：
    from relevance import match_keywords, is_relevant
    match_keywords(title + ' ' + summary)   # 命中了几个不同的相关词
    is_relevant(title)                        # 至少命中 1 个
"""
import re

# 中文相关词：子串匹配
CJK_KEYWORDS = [
    '前端', '前端部署', '前端开发', '前端工程化', '前端自动化', '前端架构',
    '智能前端', '大模型', '智能体', '工程化', '部署', '容器化', '边缘计算',
    '教学', '源码', '全栈', '小程序', '开源', '实战', '性能优化', '编译',
]

# 英文/缩写相关词：单词边界匹配
ASCII_KEYWORDS = [
    'FDE', 'AI', 'LLM', 'Agent', 'MCP', 'DevOps', 'Serverless', 'CI/CD',
    'MaxKB', 'Vercel', 'Netlify', 'Cloudflare', 'Workers', 'Copilot',
    'Cursor', 'Astro', 'Hono', 'Next.js', 'React', 'Vue', 'TypeScript',
    'Node.js', 'Kubernetes', 'WebAssembly', 'WASM', 'Rust', 'GitHub',
]

# 预编译好的正则，避免每篇文章都重新编译
_ASCII_PATTERNS = [
    (kw, re.compile(r'(?<![A-Za-z0-9])' + re.escape(kw) + r'(?![A-Z0-9])', re.I))
    for kw in ASCII_KEYWORDS
]


def match_keywords(text: str) -> set:
    """返回文本里命中的相关词集合"""
    if not text:
        return set()
    hits = set()
    for kw in CJK_KEYWORDS:
        if kw in text:
            hits.add(kw)
    for kw, pattern in _ASCII_PATTERNS:
        if pattern.search(text):
            hits.add(kw)
    return hits


def count_keywords(text: str) -> int:
    """命中了几个不同的相关词"""
    return len(match_keywords(text))


def is_relevant(text: str, min_hits: int = 1) -> bool:
    """是否相关（默认至少命中 1 个）"""
    return count_keywords(text) >= min_hits
