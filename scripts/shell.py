"""全站外壳（导航 / 面包屑 / 页脚 / 移动端 CTA）的唯一来源。

2026-10-30 商业化改版：原来每个页面各写一份导航，
16 个页面有 4 种导航样式（首页 17 条平铺、A 组 7 条、B 组 6 条、深度学习页深色自定义），
链接还有 3 个 `href="#"` 死链。现在统一成一份模板，脚本 `sync-shell.py` 负责灌进各页面。

改导航只改这里，跑一次 `python scripts/sync-shell.py` 全站生效。
"""

import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── 备案号：拿到工信部备案后填这里（例如 "京ICP备2026000000号"），页脚会自动显示 ──
ICP = ""

EMAIL = "2949465671@qq.com"
WECHAT = "2949465671"

# ── 导航结构 ──
# 下拉组：标题 + (链接, 名称, 一句话说明)
NAV_GROUPS = [
    ("课程体系", [
        ("index.html#course", "课程总览", "9 章体系一览"),
        ("syllabus.html", "完整课程大纲", "章节详情 + 示例 Prompt"),
        ("index.html#practice", "6 步实操", "从部署到嵌入全程"),
        ("index.html#scenarios", "5 大企业场景", "客服 / 备课 / 文献 / 知识库 / 政务"),
    ]),
    ("专题模块", [
        ("dl-course.html", "深度学习专题", "9 章讲解 + 7 大实验"),
        ("object-detection.html", "目标检测专题", "30 篇论文精读 + 9 张架构图"),
        ("fde-skills.html", "FDE 技能图谱", "能力矩阵与自评"),
        ("fde-jobs.html", "招聘需求", "岗位画像与技能要求"),
    ]),
    ("资源中心", [
        ("index.html#news", "教学文章", "持续更新的实战文章"),
        ("latest.html", "最新动态", "AI 热点与课程更新"),
        ("index.html#download", "资料下载", "PPT / 讲义 / 源码"),
        ("faq.html", "常见问题", "学员最关心的问题"),
    ]),
]

# 平铺项：课程页之外的 4 个入口
NAV_FLAT = [
    ("cases.html", "客户案例"),
    ("membership.html", "会员价格"),
    ("enterprise.html", "企业服务"),
    ("about.html", "关于我们"),
]

# 每个页面的中文名，用于面包屑
PAGE_TITLE = {
    "index.html": "首页",
    "syllabus.html": "课程大纲",
    "dl-course.html": "深度学习专题",
    "object-detection.html": "目标检测专题",
    "cases.html": "客户案例",
    "membership.html": "会员价格",
    "enterprise.html": "企业服务",
    "about.html": "关于我们",
    "trial.html": "预约演示",
    "faq.html": "常见问题",
    "latest.html": "最新动态",
    "fde-jobs.html": "招聘需求",
    "fde-skills.html": "FDE 技能图谱",
    "user.html": "个人中心",
    "article.html": "文章详情",
}

# 不灌外壳的页面（后台控制台等独立页面）
SKIP = {"admin.html"}


def _norm_href(href):
    """把 index.html#course 这种带锚点的链接归一成文件名，用于判断当前页高亮。"""
    return href.split("#")[0]


def _region(name, html):
    """给外壳区域套上注释标记。

    sync 时靠这对标记整块定位、整块替换 —— 没有标记就只能靠「插在 </body> 前」
    这种追加式写法，脚本一多跑一次就会多一份重复块
    （2026-10-30 就是这么积出 5 份重复的 .mcta 和面包屑的）。
    """
    return "<!-- site:%s -->\n%s\n<!-- /site:%s -->" % (name, html.strip(), name)


def build_nav(page):
    """生成导航 HTML。page = 当前页文件名。

    首页内部的锚点用 #course（能平滑滚动、能高亮），
    其他页面用 index.html#course（跳回首页的对应区块）。
    """
    home = "" if page == "index.html" else "index.html"

    def link(href):
        """把导航配置里的 index.html#xxx 换成当前页适用的写法。"""
        if href.startswith("index.html#"):
            frag = href.split("#", 1)[1]
            return "#" + frag if home == "" else href
        return href

    parts = []
    parts.append('<nav class="navbar" id="site-nav">')
    parts.append('  <div class="nav-container">')
    parts.append('    <a class="nav-logo" href="index.html">')
    parts.append('      <span class="logo-dot">M</span>')
    parts.append('      <span>MaxKB · FDE 教学</span>')
    parts.append('    </a>')
    parts.append('    <button class="hamburger" id="nav-hamburger" aria-label="展开菜单" aria-expanded="false">☰</button>')
    parts.append('    <div class="nav-links" id="nav-links">')

    parts.append('      <a href="index.html"%s>首页</a>'
                 % (' class="active"' if page == "index.html" else ''))

    for gi, (label, items) in enumerate(NAV_GROUPS):
        group_active = any(_norm_href(link(h)) == page for h, _, _ in items)
        parts.append('      <div class="nav-item has-drop">')
        parts.append('        <button class="nav-drop-btn" aria-haspopup="true" aria-expanded="false">'
                     + label + ' <span class="caret">▾</span></button>')
        parts.append('        <div class="nav-drop">')
        for href, name, desc in items:
            active = ' class="active"' if _norm_href(link(href)) == page else ''
            parts.append('          <a href="%s"%s><b>%s</b><span>%s</span></a>'
                         % (link(href), active, name, desc))
        parts.append('        </div>')
        parts.append('      </div>')

    for href, name in NAV_FLAT:
        active = ' class="active"' if href == page else ''
        parts.append('      <a href="%s"%s>%s</a>' % (href, active, name))

    parts.append('      <a href="trial.html" class="nav-cta">预约演示 →</a>')
    parts.append('    </div>')
    parts.append('  </div>')
    parts.append('  <div class="scroll-progress" id="scroll-progress"></div>')
    parts.append('</nav>')
    return _region("nav", "\n".join(parts))


def build_statusbar():
    """顶部会员状态条。script.js 会按登录状态改写它的内容。"""
    return _region("statusbar",
                   '<div id="top-status-bar" class="site-statusbar">\n'
                   '  <span id="status-text">💎 未登录 · 访问全部资源需会员</span>\n'
                   '  <a href="membership.html">👤 登录 / 注册</a>\n'
                   '</div>')


def build_crumb(page):
    """面包屑：首页 / 当前页。首页自己不需要。"""
    if page == "index.html":
        return ""
    title = PAGE_TITLE.get(page, "页面")
    return _region("crumb",
                   '<nav class="crumb" aria-label="面包屑">\n'
                   '  <a href="index.html">首页</a>\n'
                   '  <span class="sep">/</span>\n'
                   '  <span class="cur">%s</span>\n'
                   '</nav>' % title)


def build_mcta():
    """移动端吸底 CTA —— 商业站转化率最直接的一块。"""
    return _region("mcta",
                   '<div class="mcta">\n'
                   '  <div class="mcta-info">\n'
                   '    <div class="mcta-price">¥99 / 年起</div>\n'
                   '    <div class="mcta-note">标准会员 · 7 天无理由退款</div>\n'
                   '  </div>\n'
                   '  <a href="membership.html" class="btn btn-primary">开通会员</a>\n'
                   '  <a href="trial.html" class="btn btn-secondary">预约演示</a>\n'
                   '</div>')


def build_totop():
    """返回顶部按钮。"""
    return _region("totop",
                   '<button class="to-top" id="to-top" type="button" aria-label="返回顶部">↑</button>')


FOOTER_COLS = [
    ("课程", [
        ("index.html#course", "课程总览"),
        ("syllabus.html", "完整课程大纲"),
        ("index.html#practice", "6 步实操"),
        ("index.html#scenarios", "5 大企业场景"),
        ("membership.html", "会员价格与权益"),
    ]),
    ("专题与资源", [
        ("dl-course.html", "深度学习专题"),
        ("object-detection.html", "目标检测专题"),
        ("latest.html", "最新动态"),
        ("index.html#news", "教学文章"),
        ("index.html#download", "资料下载"),
    ]),
    ("支持与合作", [
        ("enterprise.html", "企业服务"),
        ("cases.html", "客户案例"),
        ("trial.html", "预约演示"),
        ("faq.html", "常见问题"),
        ("about.html", "关于小陶老师"),
    ]),
]

FOOTER_TRUST = [
    ("🛡", "7 天无理由退款"),
    ("💬", "工作日 24h 答疑"),
    ("🧾", "支持企业发票"),
    ("🔓", "GPL v3 可商用"),
    ("🔒", "数据本地存储"),
]


def build_footer():
    """全站统一页脚。"""
    p = []
    p.append('<footer class="footer">')
    p.append('  <div class="footer-content">')
    p.append('    <div class="footer-brand">')
    p.append('      <div class="nav-logo">')
    p.append('        <span class="logo-dot">M</span>')
    p.append('        <span>MaxKB · FDE 教学</span>')
    p.append('      </div>')
    p.append('      <p>基于 1Panel-dev/MaxKB 的开源企业级智能体平台教学课程。'
             '理论 30% + 实操 50% + 场景 20% 三段式教学，配套课件、源码与部署文档。</p>')
    p.append('      <div class="footer-contact">')
    p.append('        <div>📧 邮箱：<a href="mailto:%s">%s</a></div>' % (EMAIL, EMAIL))
    p.append('        <div>💬 微信：%s</div>' % WECHAT)
    p.append('        <div>🌐 开源项目：'
             '<a href="https://github.com/1Panel-dev/MaxKB" target="_blank" rel="noopener">1Panel-dev/MaxKB</a></div>')
    p.append('      </div>')
    p.append('    </div>')
    for title, links in FOOTER_COLS:
        p.append('    <div class="footer-col">')
        p.append('      <h4>%s</h4>' % title)
        for href, name in links:
            p.append('      <a href="%s">%s</a>' % (href, name))
        p.append('    </div>')
    p.append('  </div>')

    p.append('  <div class="footer-trust">')
    for icon, text in FOOTER_TRUST:
        p.append('    <span class="ft-item">%s <b>%s</b></span>' % (icon, text))
    p.append('  </div>')

    p.append('  <div class="footer-legal">')
    p.append('    <span>© 2026 小陶老师 · 由 AI 小 Q 辅助设计 · 课程资料基于 GPL v3 开源</span>')
    if ICP:
        p.append('    <span class="dot">·</span>')
        p.append('    <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener">%s</a>' % ICP)
    p.append('    <span class="dot">·</span>')
    p.append('    <a href="faq.html">购买须知</a>')
    p.append('    <span class="dot">·</span>')
    p.append('    <a href="about.html">关于小陶老师</a>')
    p.append('  </div>')
    p.append('</footer>')
    return _region("footer", "\n".join(p))


def read(path):
    return io.open(path, encoding="utf-8").read()


def write(path, s):
    io.open(path, "w", encoding="utf-8", newline="\n").write(s)


def strip_tags(html):
    return re.sub(r"<[^>]+>", "", html)
