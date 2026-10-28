#!/usr/bin/env python3
"""
FDE 文章 AI 重写脚本
调用 MINIMAX_API_KEY → 重写 + 摘要 + 加小陶老师视角
"""
import json
import os
import sys
import requests
from datetime import datetime
from pathlib import Path

SITE_DIR = Path(os.environ.get("SITE_DIR", Path(__file__).resolve().parent.parent.parent))
WORK_DIR = Path(os.environ.get("WORK_DIR", "/root/.openclaw/workspace/projects/maxkb-course-site"))
CANDIDATES_DIR = WORK_DIR / "fde-candidates"
ARTICLES_DIR = SITE_DIR / "articles"
API_KEY = os.environ.get('MINIMAX_API_KEY', '')
API_BASE = os.environ.get('MINIMAX_API_BASE', 'https://api.minimaxi.com')

def rewrite_with_ai(title, summary, source):
    """调用 LLM API 重写文章。

    失败时返回 None —— 绝不返回占位文本。
    以前这里失败会返回「（重写失败：xxx）」这种字符串，它能通过后面的
    关键词审核，于是「重写失败」几个字被当成正文发到了线上。
    """
    if not API_KEY:
        print(f"❌ 未配置 MINIMAX_API_KEY，跳过重写：{title[:30]}")
        return None

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
            f'{API_BASE}/v1/text/chatcompletion_v2',
            headers={'Authorization': f'Bearer {API_KEY}'},
            json={
                'model': 'MiniMax-Text-01',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.7
            },
            timeout=30
        )
        data = resp.json()
        # MiniMax 的业务错误不走 HTTP 状态码：HTTP 200 + base_resp.status_code != 0
        # （比如 key 无效时返回 status_code 2049「invalid api key」）
        base = data.get('base_resp') or {}
        code = base.get('status_code')
        if code not in (0, None):
            raise RuntimeError(base.get('status_msg') or f'API 返回 status_code={code}')
        content = data['choices'][0]['message']['content']
        if not content or len(content.strip()) < 50:
            raise RuntimeError('返回内容过短，判定为失败')
        return content
    except Exception as e:
        print(f"❌ 重写失败，跳过本文：{e}")
        return None

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
    failed = 0
    for i, c in enumerate(top5, 1):
        print(f"\n【{i}/{len(top5)}】{c['title'][:40]}...")
        content = rewrite_with_ai(c['title'], c.get('summary', ''), c['source'])
        if not content:
            failed += 1
            continue
        rewritten.append({
            'title': c['title'],
            'source': c['source'],
            'url': c['url'],
            'content': content
        })

    if not rewritten:
        # 一篇都没写成功就不要生成待审文件 —— 审核环节会把它当成正常文章放行
        print(f"\n❌ {failed}/{len(top5)} 篇全部重写失败，不生成待审核文件")
        sys.exit(1)

    # 输出到待审核目录
    output = WORK_DIR / "fde-pending"
    output.mkdir(parents=True, exist_ok=True)
    pending_file = output / f"pending_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(pending_file, 'w', encoding='utf-8') as f:
        json.dump(rewritten, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 重写完成 {len(rewritten)} 篇（失败 {failed} 篇），待审核: {pending_file}")

if __name__ == '__main__':
    main()
