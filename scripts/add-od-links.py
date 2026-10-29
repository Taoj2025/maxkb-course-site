"""把「目标检测专题」入口挂到全站导航 / 首页入口卡 / sitemap。

用法：python scripts/add-od-links.py
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LINK = '<a href="object-detection.html" style="color:#5CC8B0; font-weight:700;">🎯 目标检测</a>'
LINK_DL = '<a href="object-detection.html" style="color:#5CC8B0; font-weight:600; text-decoration:none; font-size:14px;">目标检测</a>'

# 页面 -> 锚点（插到这条链接之后）
NAVS = {
    "index.html": 'href="dl-course.html"',
    "syllabus.html": 'href="syllabus.html"',
    "about.html": 'href="index.html#course"',
    "cases.html": 'href="index.html#course"',
    "enterprise.html": 'href="index.html#course"',
    "membership.html": 'href="index.html#course"',
    "trial.html": 'href="index.html#course"',
    "user.html": 'href="index.html#course"',
    "faq.html": 'href="index.html"',
    "latest.html": 'href="index.html"',
}


def add_nav_link(path, anchor, link):
    p = os.path.join(ROOT, path)
    s = io.open(p, encoding="utf-8").read()
    if "object-detection.html" in s:
        print("skip (已存在) %s" % path)
        return
    m = re.search(r'<a\s[^>]*%s[^>]*>.*?</a>' % re.escape(anchor), s, re.S)
    if not m:
        print("!! 未找到锚点 %s in %s" % (anchor, path))
        return
    s = s[:m.end()] + link + s[m.end():]
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("ok  nav  %s" % path)


def add_dl_course_nav():
    p = os.path.join(ROOT, "dl-course.html")
    s = io.open(p, encoding="utf-8").read()
    if "object-detection.html" in s:
        print("skip (已存在) dl-course.html")
        return
    anchor = '<a href="dl-course.html" style="color:#FCD34D; font-weight:600; text-decoration:none; font-size:14px;">深度学习</a>'
    m = re.search(r'<a\s[^>]*href="dl-course\.html"[^>]*>.*?</a>', s, re.S)
    if not m:
        print("!! dl-course.html 锚点未找到")
        return
    s = s[:m.end()] + "\n      " + LINK_DL + s[m.end():]
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("ok  nav  dl-course.html")


def add_index_card():
    """首页：深度学习入口卡后面加一张目标检测专题卡。"""
    p = os.path.join(ROOT, "index.html")
    s = io.open(p, encoding="utf-8").read()
    if "🎯 目标检测 · 从原理到发论文" in s:
        print("skip (已存在) index.html 卡片")
        return
    anchor = '立即开始深度学习 →</a>\n  </div>\n</section>'
    if anchor not in s:
        print("!! index.html 深度学习卡片锚点未找到")
        return
    card = '''立即开始深度学习 →</a>
  </div>
</section>

<!-- 🎯 目标检测专题入口卡 -->
<section style="padding: 0 32px; margin: 60px auto;">
  <div style="background: linear-gradient(135deg, #0F172A 0%, #5B2EBF 55%, #0D9488 100%); color: white; padding: 48px 32px; border-radius: 24px; max-width: 1080px; margin: 0 auto; text-align: center; box-shadow: 0 16px 48px rgba(13, 148, 136, 0.28);">
    <span style="display: inline-block; background: rgba(92, 200, 176, 0.2); border: 2px solid #5CC8B0; color: #5CC8B0; padding: 6px 20px; border-radius: 999px; font-weight: 600; font-size: 14px; margin-bottom: 16px;">专题模块 · arXiv 近三年文献精读</span>
    <h3 style="font-size: 36px; margin: 16px 0;">🎯 目标检测 · 从原理到发论文</h3>
    <p style="font-size: 16px; max-width: 760px; margin: 0 auto 24px; opacity: 0.95; line-height: 1.7;">30 篇近三年 arXiv 论文逐篇拆解核心思想与创新点 · 9 张自绘原理架构图 · 4 个可复现实验 · 6 个可直接开题的科研方向</p>
    <div style="display: flex; gap: 24px; justify-content: center; flex-wrap: wrap; margin-bottom: 24px;">
      <div style="text-align: center;"><div style="font-size: 32px; font-weight: 700; color: #5CC8B0;">30</div><div style="font-size: 12px; opacity: 0.8;">篇论文精读</div></div>
      <div style="text-align: center;"><div style="font-size: 32px; font-weight: 700; color: #5CC8B0;">9</div><div style="font-size: 12px; opacity: 0.8;">张原理架构图</div></div>
      <div style="text-align: center;"><div style="font-size: 32px; font-weight: 700; color: #5CC8B0;">5</div><div style="font-size: 12px; opacity: 0.8;">条研究主线</div></div>
      <div style="text-align: center;"><div style="font-size: 32px; font-weight: 700; color: #5CC8B0;">4</div><div style="font-size: 12px; opacity: 0.8;">个复现实验</div></div>
      <div style="text-align: center;"><div style="font-size: 32px; font-weight: 700; color: #5CC8B0;">6</div><div style="font-size: 12px; opacity: 0.8;">个开题方向</div></div>
    </div>
    <div class="dl-figure">
      <img src="assets/images/08_检测器通用架构.png"
           alt="目标检测器通用架构解剖图：输入图像经过 Backbone 骨干提取 C3/C4/C5 多尺度特征，经 Neck 特征融合得到 P3/P4/P5，最后由 Head 预测头输出框、类别与置信度"
           width="1427" height="767" loading="lazy"
           data-figure="assets/images/08_检测器通用架构.png"
           data-caption="图 8 · 目标检测器通用架构：Backbone / Neck / Head 三段式">
    </div>
    <a href="object-detection.html" style="display: inline-block; margin-top: 24px; background: #5CC8B0; color: #0F172A; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 16px;">进入目标检测专题 →</a>
  </div>
</section>'''
    s = s.replace(anchor, card)
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("ok  card index.html")


def add_sitemap():
    p = os.path.join(ROOT, "sitemap.xml")
    s = io.open(p, encoding="utf-8").read()
    if "object-detection.html" in s:
        print("skip (已存在) sitemap.xml")
        return
    entry = '''  <url>
    <loc>https://taotaoedu.ltd/object-detection.html</loc>
    <lastmod>2026-10-30</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.85</priority>
  </url>
'''
    s = s.replace("</urlset>", entry + "</urlset>")
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("ok  sitemap.xml")


for f, a in NAVS.items():
    add_nav_link(f, a, LINK)
add_dl_course_nav()
add_index_card()
add_sitemap()
