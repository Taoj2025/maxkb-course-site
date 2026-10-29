#!/usr/bin/env python3
"""把各页面里手写的行内分区样式，统一换成 .sec 系列类。

为什么做这件事：
  同一件事，16 个页面里出现了 20 多种行内写法（有的 max-width:100%、
  有的没有；有的 padding 80px、有的 60px；背景色 white / #FAFAFB / 渐变各写一遍）。
  后果是改一次版式要挨个页面改，还容易漏掉 —— 这正是「布局不统一」的根源。

  .sec / .sec-wrap 这套类定在 style.css 里，全站只有一份定义。

用法：python scripts/normalize-sections.py
"""

import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shell  # noqa: E402

# 行内 style → 目标类名
# 只匹配完全一样的写法，宁可漏改也不要改坏别的页面
SECTION_RULES = [
    # 全幅白底分区
    (r'style="background:\s*white;\s*max-width:\s*100%;\s*padding:\s*80px 32px;"', "sec white"),
    (r'style="background:\s*white;\s*max-width:\s*100%;\s*padding:\s*80px 32px;\s*"', "sec white"),
    (r'style="background:\s*white;\s*padding:\s*80px 32px;"', "sec white"),
    (r'style="padding:\s*80px 32px;\s*background:\s*white;"', "sec white"),
    (r'style="background:\s*#fff;\s*max-width:\s*100%;\s*padding:\s*80px 32px;"', "sec white"),
    # 浅灰渐变分区
    (r'style="background:\s*linear-gradient\(180deg,\s*#FAFAFB,\s*white\);\s*padding:\s*80px 32px;"', "sec gray"),
    (r'style="background:\s*linear-gradient\(180deg,\s*#FAFAFB,\s*white\);\s*max-width:\s*100%;\s*padding:\s*80px 32px;"', "sec gray"),
    (r'style="background:\s*linear-gradient\(180deg,\s*#faf8ff 0%,\s*#ffffff 100%\);\s*max-width:\s*100%;\s*padding:\s*80px 32px;"', "sec tint"),
    (r'style="max-width:\s*100%;\s*padding:\s*60px 32px;\s*background:\s*linear-gradient\(180deg,\s*#FAFAFB,\s*white\);"', "sec gray"),
]

# 内层 1280px 容器 → .sec-wrap
#
# ⚠️ 这里只放类名，不要写整条 class="..."！
#    早期版本写的是 'class="sec-wrap"'，而下面的替换逻辑又自己拼了一次
#    class="..."，两层叠在一起生成出 class="class="sec-wrap"" ——
#    属性嵌套，浏览器只认到 class="class="，.sec-wrap 的 max-width:1280px
#    根本没生效，分区内容直接顶到屏幕两边（2026-10-30 批量体检时发现）。
WRAP_RULES = [
    (r'style="max-width:\s*1280px;\s*margin:\s*0 auto;"', "sec-wrap"),
    (r'style="max-width:1280px;\s*margin:0 auto;"', "sec-wrap"),
]

# 修掉历史上生成出来的坏属性
BAD_CLASS = re.compile(r'class="class="([^"]*)""')


def normalize(page):
    path = os.path.join(ROOT, page)
    s = io.open(path, encoding="utf-8").read()
    orig = s

    # 0) 先修坏属性（要在下面两条规则之前 —— 修好之后 div 已经有 class="，
    #    下面的正则会自动跳过它，不会再重复转换）
    s = BAD_CLASS.sub(lambda m: 'class="%s"' % m.group(1), s)

    for pat, cls in SECTION_RULES:
        # 已有 class 的 section 就不动
        s = re.sub(
            r"<section(?![^>]*\bclass=)([^>]*?)" + pat,
            lambda m, cls=cls: '<section class="%s"' % cls + m.group(1),
            s)

    for pat, cls in WRAP_RULES:
        s = re.sub(
            r"<div(?![^>]*\bclass=)([^>]*?)" + pat,
            lambda m, cls=cls: '<div class="%s"' % cls + m.group(1),
            s)

    # 收尾：属性后面多出来的空格（原来生成的是 <section class="sec gray" >）
    s = re.sub(r'((?:class|id)="[^"]*")\s+>', r'\1>', s)

    return s, orig


def main():
    pages = [p for p in sorted(os.listdir(ROOT))
             if p.endswith(".html") and not p.endswith(".template.html")
             and p not in shell.SKIP]
    changed = 0
    for page in pages:
        new, old = normalize(page)
        if new != old:
            shell.write(os.path.join(ROOT, page), new)
            changed += 1
            print("  ✅ %-24s 分区样式已统一" % page)
    print()
    print("✅ 处理 %d 个页面，%d 个有改动" % (len(pages), changed))


if __name__ == "__main__":
    main()
