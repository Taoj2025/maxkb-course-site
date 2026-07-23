#!/usr/bin/env python3
"""
FDE 文章 AI 重写脚本
调用 MINIMAX_API_KEY → 重写 + 摘要 + 加小陶老师视角
"""
import json
import os
import requests
from datetime import datetime
from pathlib import Path

CANDIDATES_DIR = Path('/root/.openclaw/workspace/projects/maxkb-course-site/fde-candidates')
ARTICLES_DIR = Path('/root/.openclaw/workspace/projects/maxkb-course-site/site/articles')
API_KEY = os.environ.get('MINIMAX_API_KEY', '')

def rewrite_with_ai(title, summary, source):
    """调用 LLM API 重写文章"""
    if not API_KEY:
        return f"{title}\n\n（摘要）{summary}\n\n（来源：{source}）"
    
    prompt = f"""你是小陶老师（广州华商学院大数据专业教师，专攻 MaxKB FDE 培训）。

请把以下 FDE（前端部署开发工程师）相关文章改写为面向高校学生 / 教师的教学博客。

原标题：{title}
原摘要：{summary}
来源：{source}

要求：
1. 用通俗易懂的语言（教师视角）
2. 加入教学场景说明（学生怎么学 / 教师怎么用）
3. 关联 MaxKB 教学（如适用）
4. 字数 200-400 字
5. 用 Markdown 格式
6. 末尾注明「来源：{source}」

请输出 Markdown 正文（不含 front matter）。"""
    
    try:
        resp = requests.post(
            'https://api.minimax.chat/v1/text/chatcompletion_v2',
            headers={'Authorization': f'Bearer {API_KEY}'},
            json={
                'model': 'MiniMax-Text-01',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.7
            },
            timeout=30
        )
        return resp.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"{title}\n\n{summary}\n\n（重写失败：{e}）"

def main():
    print("=" * 50)
    print(f"🤖 AI 重写 · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 找最新候选
    candidates_files = sorted(CANDIDATES_DIR.glob('candidates_*.json'), reverse=True)
    if not candidates_files:
        print("❌ 未找到候选文件，请先运行 fetch_articles.py")
        return
    
    latest = candidates_files[0]
    with open(latest, 'r', encoding='utf-8') as f:
        candidates = json.load(f)
    
    # 取前 5 篇
    top5 = candidates[:5]
    print(f"📋 准备重写 {len(top5)} 篇")
    
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    
    rewritten = []
    for i, c in enumerate(top5, 1):
        print(f"\n【{i}/{len(top5)}】{c['title'][:40]}...")
        content = rewrite_with_ai(c['title'], c.get('summary', ''), c['source'])
        rewritten.append({
            'title': c['title'],
            'source': c['source'],
            'url': c['url'],
            'content': content
        })
    
    # 输出到待审核目录
    output = Path('/root/.openclaw/workspace/projects/maxkb-course-site/fde-pending')
    output.mkdir(parents=True, exist_ok=True)
    pending_file = output / f"pending_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(pending_file, 'w', encoding='utf-8') as f:
        json.dump(rewritten, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 重写完成，待审核: {pending_file}")

if __name__ == '__main__':
    main()
