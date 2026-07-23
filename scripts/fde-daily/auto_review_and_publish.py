#!/usr/bin/env python3
"""
FDE 文章 · AI 自动审核 + 自动发布
"""
import json
import os
import re
import requests
from datetime import datetime
from pathlib import Path

PENDING_DIR = Path('/root/.openclaw/workspace/projects/maxkb-course-site/fde-pending')
ARTICLES_DIR = Path('/root/.openclaw/workspace/projects/maxkb-course-site/site/articles')
API_KEY = os.environ.get('MINIMAX_API_KEY', '')
PUSH_TOKEN = os.environ.get("GITHUB_PAT_TOKEN", os.environ.get("PUSH_TOKEN", ""))
REPO = "Taoj2025/maxkb-course-site"

BAD_KEYWORDS = ['博彩', '赌博', '色情', '广告', '营销', '色情', '标题党']

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
            resp = requests.post(
                'https://api.minimax.chat/v1/text/chatcompletion_v2',
                headers={'Authorization': f'Bearer {API_KEY}'},
                json={'model': 'MiniMax-Text-01', 'messages': [{'role': 'user', 'content': prompt}], 'temperature': 0.3},
                timeout=15
            )
            score_text = resp.json()['choices'][0]['message']['content'].strip()
            score = float(re.search(r'\d+\.?\d*', score_text).group())
            if score < 3.0:
                return False, f"AI 评分过低：{score}"
            return True, f"AI 评分：{score}"
        except Exception as e:
            pass  # AI 失败时降级为基础规则
    
    # 3. 兜底：基于关键词相关性
    score = sum(1 for kw in ['FDE', '前端', 'AI', 'LLM', '工程化', '部署', '开发', 'MaxKB', 'Vercel', '教学'] if kw in (title + content[:500]))
    if score < 2:
        return False, f"相关性低：命中 {score} 个关键词"
    return True, f"关键词命中：{score}"

def push_to_github(filepath, message):
    """推送到 GitHub"""
    FILE_B64 = Path(filepath).read_bytes()
    import base64
    FILE_B64 = base64.b64encode(FILE_B64).decode()
    sha_resp = requests.get(
        f"https://api.github.com/repos/{REPO}/contents/{filepath}",
        headers={'Authorization': f'token {PUSH_TOKEN}'},
        timeout=10
    )
    sha = sha_resp.json().get('sha', '') if sha_resp.status_code == 200 else ''
    data = {'message': message, 'content': FILE_B64, 'branch': 'main'}
    if sha:
        data['sha'] = sha
    resp = requests.put(
        f"https://api.github.com/repos/{REPO}/contents/{filepath}",
        headers={'Authorization': f'token {PUSH_TOKEN}', 'Content-Type': 'application/json'},
        json=data, timeout=30
    )
    return resp.status_code

def publish_article(article, idx):
    """发布单篇文章到网站"""
    title_slug = re.sub(r'[^\w\s-]', '', article['title'])[:30].strip().replace(' ', '-').lower()
    date_str = datetime.now().strftime('%Y%m%d')
    filename = f"fde-{date_str}-{idx:02d}-{title_slug}.md"
    filepath = ARTICLES_DIR / filename
    
    # 写入 Markdown
    md_content = f"""---
title: "{article['title']}"
source: "{article['source']}"
source_url: "{article['url']}"
date: "{datetime.now().strftime('%Y-%m-%d')}"
auto: true
---

{article['content']}

---

*本文由小Q自动抓取 + AI 重写 · 来源：[{article['source']}]({article['url']})*
"""
    filepath.write_text(md_content, encoding='utf-8')
    
    # 推 GitHub
    github_path = f"articles/{filename}"
    code = push_to_github(github_path, f"auto: FDE 每日文章 · {filename}")
    return filename, code

def main():
    print("=" * 50)
    print(f"🤖 AI 自动审核 + 自动发布 · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 找最新待审文件
    pending_files = sorted(PENDING_DIR.glob('pending_*.json'), reverse=True)
    if not pending_files:
        print("❌ 无待审核内容，请先运行 rewrite_articles.py")
        return
    
    latest = pending_files[0]
    with open(latest, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    print(f"📋 待审 {len(articles)} 篇")
    
    passed = []
    rejected = []
    for i, art in enumerate(articles, 1):
        ok, reason = ai_review(art)
        if ok:
            print(f"  ✅ [{i}] 通过 · {reason} · {art['title'][:30]}")
            passed.append((i, art, reason))
        else:
            print(f"  ❌ [{i}] 拒绝 · {reason} · {art['title'][:30]}")
            rejected.append((i, art, reason))
    
    print(f"\n📊 通过 {len(passed)} 篇 / 拒绝 {len(rejected)} 篇")
    
    # 自动发布通过的
    if passed:
        print("\n🚀 自动发布...")
        for idx, (i, art, reason) in enumerate(passed, 1):
            filename, code = publish_article(art, idx)
            print(f"  📝 {filename} → HTTP {code}")
        
        # 更新 articles.json
        from datetime import datetime
        articles_json_path = Path('/root/.openclaw/workspace/projects/maxkb-course-site/site/articles.json')
        if articles_json_path.exists():
            with open(articles_json_path, 'r', encoding='utf-8') as f:
                articles_data = json.load(f)
            
            for idx, (i, art, reason) in enumerate(passed, 1):
                filename = f"fde-{datetime.now().strftime('%Y%m%d')}-{idx:02d}-{re.sub(r'[^\\w\\s-]', '', art['title'])[:30].strip().replace(' ', '-').lower()}.md"
                articles_data.append({
                    'title': art['title'],
                    'slug': filename.replace('.md', ''),
                    'source': art['source'],
                    'source_url': art['url'],
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'auto': True,
                    'preview': art['content'][:150]
                })
            
            with open(articles_json_path, 'w', encoding='utf-8') as f:
                json.dump(articles_data, f, ensure_ascii=False, indent=2)
            
            code = push_to_github('articles.json', f"auto: 更新 articles.json · {len(passed)} 篇")
            print(f"  📋 articles.json → HTTP {code}")

if __name__ == '__main__':
    main()
