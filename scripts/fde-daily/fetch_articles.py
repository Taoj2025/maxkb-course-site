#!/usr/bin/env python3
"""
FDE（前端部署开发工程师）每日文章抓取脚本
数据源：新榜 + 微博热搜 + 知乎 + 微信公众号
作者：小 Q 为小陶老师定制 · 2026-07-24
"""
import json
import requests
import feedparser
from datetime import datetime
from pathlib import Path

OUT_DIR = Path('/root/.openclaw/workspace/projects/maxkb-course-site/fde-candidates')
OUT_DIR.mkdir(parents=True, exist_ok=True)

KEYWORDS = ['FDE', '前端部署', '前端开发工程师', 'AI前端', 'LLM前端', '前端AI', '智能前端', '前端工程化', 'Vercel', 'Netlify', '前端自动化', 'CI/CD前端']

def fetch_xinbang():
    """新榜 API（公众号文章）"""
    # 注：需注册 https://www.newrank.cn/ 开发者账号
    # 简化版：使用搜索 API（公开 RSS）
    results = []
    for kw in ['前端开发', 'AI 前端', '前端部署']:
        try:
            url = f"https://www.newrank.cn/rank/search?key={kw}&type=article"
            # 实际生产需用新榜开放 API（newrank.cn/open）
            # 这里只占位，告知用户如何接入
        except Exception as e:
            print(f"  ⚠ 新榜抓取失败: {e}")
    return results

def fetch_weibo():
    """微博热搜"""
    try:
        resp = requests.get('https://weibo.com/ajax/side/hotSearch', timeout=10)
        data = resp.json().get('data', {}).get('realtime', [])
        results = []
        for item in data[:30]:  # 前 30 个热搜
            word = item.get('word', '')
            if any(kw.lower() in word.lower() for kw in KEYWORDS):
                results.append({
                    'title': word,
                    'source': 'weibo_hot',
                    'url': f"https://s.weibo.com/weibo?q=%23{word}%23",
                    'summary': f"微博热搜 · {word}",
                    'hot_score': item.get('num', 0),
                    'fetched_at': datetime.now().isoformat()
                })
        return results
    except Exception as e:
        print(f"  ⚠ 微博抓取失败: {e}")
        return []

def fetch_zhihu():
    """知乎热榜（公开 RSS）"""
    try:
        # 知乎热榜 RSS
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json().get('data', [])
        results = []
        for item in data[:30]:
            target = item.get('target', {})
            title = target.get('title', '') or target.get('question_title', '')
            if any(kw in title for kw in ['前端', 'FDE', 'AI', 'LLM', '工程化', '部署']):
                results.append({
                    'title': title,
                    'source': 'zhihu_hot',
                    'url': f"https://www.zhihu.com/question/{target.get('id', '')}",
                    'summary': target.get('excerpt', '')[:200],
                    'hot_score': item.get('detail_text', ''),
                    'fetched_at': datetime.now().isoformat()
                })
        return results
    except Exception as e:
        print(f"  ⚠ 知乎抓取失败: {e}")
        return []

def fetch_rss():
    """RSS 订阅源（兜底）"""
    sources = [
        ('InfoQ 前端', 'https://www.infoq.cn/feed.xml'),
        ('36氪 资讯', 'https://36kr.com/feed'),
        ('掘金', 'https://juejin.cn/feed'),
        ('GitHub Trending', 'https://mshibanami.github.io/GitHubTrendingRSS/weekly/all.xml'),
        ('V2EX 前端', 'https://www.v2ex.com/?tab=frontend&rss=1')
    ]
    results = []
    for source_name, url in sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                title = entry.get('title', '')
                if any(kw in title for kw in KEYWORDS):
                    results.append({
                        'title': title,
                        'source': f'rss_{source_name}',
                        'url': entry.get('link', ''),
                        'summary': entry.get('summary', '')[:200],
                        'published': entry.get('published', ''),
                        'fetched_at': datetime.now().isoformat()
                    })
        except Exception as e:
            print(f"  ⚠ RSS {source_name} 抓取失败: {e}")
    return results

def main():
    print("=" * 50)
    print(f"📡 FDE 文章抓取 · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    all_results = []
    
    print("【1/4】微博热搜...")
    all_results.extend(fetch_weibo())
    
    print("【2/4】知乎热榜...")
    all_results.extend(fetch_zhihu())
    
    print("【3/4】新榜 API...")
    all_results.extend(fetch_xinbang())
    
    print("【4/4】RSS 兜底源...")
    all_results.extend(fetch_rss())
    
    # 去重 + 按热度排序
    seen = set()
    unique = []
    for r in all_results:
        if r['title'] not in seen:
            seen.add(r['title'])
            unique.append(r)
    
    print(f"\n✅ 共抓取 {len(unique)} 篇不重复 FDE 文章")
    
    # 输出
    output_file = OUT_DIR / f"candidates_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)
    print(f"📁 已保存到: {output_file}")

if __name__ == '__main__':
    main()
