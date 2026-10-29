#!/usr/bin/env python3
"""把全站外壳（导航 / 状态条 / 面包屑 / 页脚 / 移动端 CTA）灌进每一个页面。

用法：python scripts/sync-shell.py            # 只在本地文件上改
      python scripts/sync-shell.py --check    # 只检查不写（CI 用，有差异就退出码 1）

改导航/页脚请改 scripts/shell.py，然后重跑这个脚本，别手改各页面。

⚠️ 这个脚本必须可重复执行（幂等）：
   早期版本用「往 </body> 前追加」的方式插吸底 CTA 和面包屑，
   结果每跑一次多一份 —— 页面上积了 5 份重复的 .mcta 和 5 个 id 重复的
   to-top 按钮（重复 ID 是无效 HTML，getElementById 只会拿到第一个）。
   现在改成「先把所有外壳区域整块删干净，再按固定位置插回去」，
   跑几次结果都一样。--check 能验证这一点。
"""

import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shell  # noqa: E402

ROOT = shell.ROOT
PAGES = [p for p in sorted(os.listdir(ROOT))
         if p.endswith(".html") and not p.endswith(".template.html")]

# ── 各页面的脚本文单 ──
# 只补「缺的那几个」，不重复加载 —— api.js / membership.js 里有顶层 const，
# 同一个页面加载两次会直接抛 "Identifier 'x' has already been declared"。
#
# 补的脚本一律不带 defer，并插在页面正文里第一个 <script> 之前：
# 页面上那些行内 <script> 会用到 window.api / MembershipStore，
# 插在它们前面才能保证全局变量已经就位。
STD_SCRIPTS = [
    'config.js', 'api.js', 'membership.js', 'script.js',
]
STD_TAG = '<script src="assets/js/%s"></script>'

# 老的行内汉堡菜单脚本 —— script.js 里已有统一实现，这段要拿掉，
# 否则两个监听器抢同一个 .open 类，会出现「点一下开了又关了」。
OLD_HAMBURGER_JS = re.compile(
    r"<script>\s*//\s*汉堡菜单.*?</script>\s*", re.S)

# fde-skills.html 里给「底部导航」写的行内样式，
# 选择器是 .nav-links，会把新的顶栏也污染掉（text-align:center、
# margin-top:40px 让导航撑到 143px 高）。这些规则整体拿掉 ——
# 底部导航已经被统一页脚取代了。
OLD_NAVLINKS_CSS = re.compile(
    r"[ \t]*\.nav-links[^{]*\{(?:[^{}]|\{[^{}]*\})*\}\n", re.S)


# ── 外壳区域：先删干净，再插回去 ──
# 每条规则负责一个区域。正则要能同时干掉两种形态：
#   1) 带 <!-- site:xxx --> 标记的（新版）
#   2) 没有标记的历史遗留版（改版前各页面各写一份的老样子）
LEGACY = [
    # 区域名, 遗留版正则
    ("statusbar", re.compile(r'<div id="top-status-bar"[^>]*>.*?</div>\s*', re.S)),
    ("nav", re.compile(r'<nav class="navbar"[^>]*>.*?</nav>\s*', re.S)),
    ("crumb", re.compile(r'<nav class="crumb"[^>]*>.*?</nav>\s*', re.S)),
    ("footer", re.compile(r'<footer[^>]*>.*?</footer>\s*', re.S)),
    # 吸底 CTA 和返回顶部是成对的，一起删（遗留版它们总是紧挨着）
    ("mcta", re.compile(
        r'<div class="mcta">.*?</div>\s*'
        r'<button class="to-top"[^>]*>.*?</button>\s*', re.S)),
    ("totop", re.compile(r'<button class="to-top"[^>]*>.*?</button>\s*', re.S)),
]


def strip_regions(s):
    """删掉所有外壳区域（不管有几份、哪种写法）。"""
    for name, legacy in LEGACY:
        # 先删带标记的
        marked = re.compile(
            r"<!--\s*site:%s\s*-->.*?<!--\s*/site:%s\s*-->\s*" % (name, name),
            re.S)
        s = marked.sub("", s)
        # 再删遗留的
        s = legacy.sub("", s)
    return s


def insert_after_body(s, html):
    """插到 <body> 标签之后。"""
    m = re.search(r"<body[^>]*>", s)
    if not m:
        raise SystemExit("❌ 找不到 <body>")
    return s[:m.end()] + "\n\n" + html + "\n\n" + s[m.end():]


def insert_before_body_end(s, html):
    """插到 </body> 之前。"""
    if "</body>" not in s:
        raise SystemExit("❌ 找不到 </body>")
    return s.replace("</body>", html + "\n\n</body>", 1)


def sync(page):
    path = os.path.join(ROOT, page)
    s = io.open(path, encoding="utf-8").read()
    orig = s

    # 1) 清理 —— 所有外壳区域先删干净，包括历史遗留的多余副本
    s = strip_regions(s)

    # 2) 头部三块：状态条 / 导航 / 面包屑，统一插在 <body> 之后
    head = shell.build_statusbar() + "\n\n" + shell.build_nav(page)
    crumb = shell.build_crumb(page)
    if crumb:
        head += "\n\n" + crumb
    s = insert_after_body(s, head)

    # 3) 尾部三块：页脚 / 吸底 CTA / 返回顶部，统一插在 </body> 之前
    tail = (shell.build_footer() + "\n\n"
            + shell.build_mcta() + "\n\n" + shell.build_totop())
    s = insert_before_body_end(s, tail)

    # 4) body 加上状态条 / 吸底 CTA 的标记类（CSS 靠它留出空间）
    #    注意要写成合法的 class="..." —— 写成 <body has-mcta> 浏览器会直接忽略
    m = re.search(r"<body([^>]*)>", s)
    attrs = m.group(1)
    # 先把这两个名字从属性串里彻底抹掉（早期版本写成过非法的 <body has-mcta>），
    # 再统一塞回合法的 class="..."
    attrs = re.sub(r"has-(?:statusbar|mcta)\b", "", attrs)
    cm = re.search(r'class="([^"]*)"', attrs)
    classes = [c for c in (cm.group(1).split() if cm else [])
               if c not in ("has-statusbar", "has-mcta")]
    for cls in ("has-statusbar", "has-mcta"):
        if cls not in classes:
            classes.append(cls)
    new_attrs = re.sub(r'\s*class="[^"]*"', "", attrs).strip()
    new_attrs = ('class="%s"' % " ".join(classes)) + ((" " + new_attrs) if new_attrs else "")
    s = s[:m.start()] + "<body %s>" % new_attrs + s[m.end():]

    # 5) 统一脚本：老的行内汉堡脚本拿掉，标准脚本去重 + 补齐
    s = OLD_HAMBURGER_JS.sub("", s)
    s = OLD_NAVLINKS_CSS.sub("", s)

    # 去重：同一个标准脚本在一个页面里只能出现一次
    # （api.js / membership.js 里有顶层 const，重复加载直接抛错）
    for f in STD_SCRIPTS:
        pat = re.compile(r'[ \t]*<script src="assets/js/%s"[^>]*></script>\n?' % re.escape(f))
        seen = [False]

        def keep_first(m, seen=seen):
            if seen[0]:
                return ""
            seen[0] = True
            return m.group(0)

        s = pat.sub(keep_first, s)

    missing = [f for f in STD_SCRIPTS if ('assets/js/%s"' % f) not in s]
    if missing:
        tags = "\n".join(STD_TAG % f for f in missing)
        # 插在正文里第一个 <script> 之前 —— 保证行内脚本用得到这些全局变量
        body_at = re.search(r"<body[^>]*>", s)
        head = s[:body_at.end()]
        rest = s[body_at.end():]
        m = re.search(r"<script\b", rest)
        if m:
            s = head + rest[:m.start()] + tags + "\n" + rest[m.start():]
        else:
            s = s.replace("</body>", tags + "\n</body>")

    # 6) fde-skills.html 的底部导航已被统一页脚取代
    s = re.sub(r"\n[ \t]*<!--\s*底部导航\s*-->\n[ \t]*<div class=\"nav-links\">.*?</div>\n",
               "\n", s, flags=re.S)

    return s, orig


def main():
    check = "--check" in sys.argv
    changed = []
    for page in PAGES:
        if page in shell.SKIP:
            print("  ⏭  %-24s 独立后台页，跳过" % page)
            continue
        new, old = sync(page)
        if new == old:
            print("  ✅ %-24s 已是最新" % page)
            continue
        changed.append(page)
        if not check:
            shell.write(os.path.join(ROOT, page), new)
        print("  %s %-24s 外壳已更新" % ("✅" if not check else "⚠️ ", page))

    print()
    if check and changed:
        print("❌ %d 个页面与 shell.py 不一致：%s" % (len(changed), ", ".join(changed)))
        sys.exit(1)
    print("✅ 共处理 %d 个页面，%d 个有改动" % (len(PAGES) - len(shell.SKIP), len(changed)))


if __name__ == "__main__":
    main()
