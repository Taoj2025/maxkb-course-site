"""把文献卡片与文献清单注入 object-detection.html。

用法：python scripts/build-object-detection-page.py

输入：
  data/object-detection-papers.json   30 篇论文的完整数据
  scripts/make-detection-cards.py      文献卡片区块（通过 import 复用）
输出：
  object-detection.html                页面里的 <!--PAPER_CARDS--> / <!--BIB_ROWS--> 占位符被替换
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "object-detection.template.html")
HTML = os.path.join(ROOT, "object-detection.html")
PAPERS = os.path.join(ROOT, "data", "object-detection-papers.json")

esc = lambda s: (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def run_cards():
    """调用 make-detection-cards.py 拿到卡片 HTML。"""
    out = subprocess.check_output(
        [sys.executable, os.path.join(ROOT, "scripts", "make-detection-cards.py")],
        cwd=ROOT,
    )
    return out.decode("utf-8")


def build_bib(papers):
    """文献清单表格行，按发表时间倒序。"""
    rows = []
    for p in sorted(papers, key=lambda x: x["published"], reverse=True):
        au = p["authors"]
        au_txt = "、".join(au[:3]) + (" 等 %d 人" % len(au) if len(au) > 3 else "")
        mark = "近三年" if p["inWindow"] else "奠基"
        rows.append(
            '      <div class="bib-row">\n'
            '        <div class="bib-id">arXiv:%s<br><span style="color:#9CA3AF">%s</span></div>\n'
            '        <div class="bib-title"><b>%s</b><br>%s<br>'
            '<span style="color:#6B7280;font-size:12px">%s · %s</span></div>\n'
            '        <div class="bib-venue">%s<br><a href="%s" target="_blank" rel="noopener">arXiv 原文 ↗</a></div>\n'
            '      </div>'
            % (esc(p["id"]), mark, esc(p["title"]), esc(p["titleZh"]),
               esc(au_txt), esc(p["published"]), esc(p["venue"]), p["arxivUrl"])
        )
    return "\n".join(rows)


def main():
    papers = json.load(io.open(PAPERS, encoding="utf-8"))
    html = io.open(TEMPLATE, encoding="utf-8").read()

    cards = run_cards()
    bib = build_bib(papers)

    if "<!--PAPER_CARDS-->" not in html:
        print("!! 找不到 <!--PAPER_CARDS--> 占位符", file=sys.stderr)
        return 1
    if "<!--BIB_ROWS-->" not in html:
        print("!! 找不到 <!--BIB_ROWS--> 占位符", file=sys.stderr)
        return 1

    html = html.replace("<!--PAPER_CARDS-->", cards.strip())
    html = html.replace("<!--BIB_ROWS-->", bib)

    io.open(HTML, "w", encoding="utf-8", newline="\n").write(html)
    print("OK  论文 %d 篇 / 卡片 %d 行 / 文献清单 %d 行" % (len(papers), cards.count("\n") + 1, len(papers)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
