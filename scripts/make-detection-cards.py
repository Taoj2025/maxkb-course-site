"""由 data/object-detection-papers.json 生成 object-detection.html 的文献卡片区块。
跑法：python scripts/make-detection-cards.py > /tmp/cards.html
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
papers = json.load(io.open(os.path.join(ROOT, "data", "object-detection-papers.json"), encoding="utf-8"))

THEME_ORDER = ["end2end", "realtime", "ovod", "foundation", "backbone"]

THEME_META = {
    "end2end": dict(
        no="01", name="端到端 DETR 系", sub="集合预测 · 匹配机制 · 回归形式",
        desc="端到端路线把检测从「先出候选再筛选」改写成「直接预测一个集合」。这条线的三年进展几乎全部集中在两处：<b>预测与 GT 怎么配对</b>（匈牙利匹配 → 密集一对一 → 图协作），以及<b>框怎么回归</b>（L1 单点 → 细粒度分布细化）。这两件事彼此正交，因此可以叠加——这正是写文章时最好讲的叙事结构。",
        figure=("11_DETR三大改进对比.png", "图 11 · DETR 系三大关键改进：DINO 改收敛、DEIM 改匹配、D-FINE 改回归"),
        ),
    "realtime": dict(
        no="02", name="实时检测", sub="把速度与精度同时往前推一格",
        desc="实时线的核心矛盾是「训练与推理不一致」和「后处理开销」这两个历史包袱。YOLOv9 用可编程梯度信息解决深层监督失效，YOLOv10 用一致性双重标签分配彻底去掉 NMS，YOLOv12 把注意力做便宜；RT-DETR 则从 DETR 一侧证明端到端也能实时。<b>三条路径互补而非互斥</b>，是可以并排写进一张对比表的。",
        figures=[
            ("12_RT-DETR混合编码器.png", "图 12 · RT-DETR 混合编码器：把 CNN 多尺度特征、AIFI 与 Transformer Encoder 融进同一条实时推理链路"),
            ("13_YOLO实时检测演进.png", "图 13 · YOLO 系近三年三个关键版本：v9 改训练信号、v10 去 NMS、v12 把注意力做便宜"),
        ],
        ),
    "ovod": dict(
        no="03", name="开放词汇检测", sub="从闭集 80 类到任意文本类别",
        desc="开放词汇检测改变了任务定义本身：类别不再由训练集给定，而是由一句文本提示给出。技术路线分成两派——<b>先检测再分类</b>（OWLv2、DetRefiner、ExDet）与<b>深度跨模态融合</b>（Grounding DINO、FlowOVD）。2026 年的新趋势是二者融合，并普遍采用「检测器 + 视觉语言模型」的双组件协作。",
        figure=("14_开放词汇检测三范式.png", "图 14 · 开放词汇检测三种主流范式：Grounding DINO / OWLv2 / YOLO-World"),
        ),
    "foundation": dict(
        no="04", name="视觉基础模型", sub="一个模型，多种任务",
        desc="Florence-2 把检测、指代、描述、密集标注统一成文本生成；SAM 2 把提示分割扩展到视频并用记忆机制保持时序一致；DINOv2 / DINOv3 则提供可冻结即用的通用视觉骨干。这一支对检测器的作用通常不是直接替换，而是<b>提供更强的特征与更强的开放词汇先验</b>。",
        figure=None),
    "backbone": dict(
        no="05", name="骨干网络", sub="特征质量决定上限",
        desc="TransNeXt 用聚合邻域注意力刻画注视点聚集特性，VMamba 用状态空间模型以线性复杂度换取全局感受野，VGTok 则把「固定 token 网格」改成「按区域变粒度」。骨干侧的变化常常比检测头更直接地影响小目标与密集目标的表现，<b>也是课程实验里最容易做出可复现消融的一环</b>。",
        figure=None),
}

esc = lambda s: (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def authors_line(a):
    if not a:
        return ""
    if len(a) <= 3:
        return "、".join(a)
    return "、".join(a[:3]) + " 等 %d 人" % len(a)


out = []
for theme in THEME_ORDER:
    items = [p for p in papers if p["theme"] == theme]
    if not items:
        continue
    items.sort(key=lambda p: p["published"])
    tm = THEME_META[theme]
    out.append('<div class="theme-block">')
    out.append('  <div class="theme-head">')
    out.append('    <div class="theme-no">%s</div>' % tm["no"])
    out.append('    <div><h3>%s</h3><div class="theme-sub">%s</div></div>' % (tm["name"], tm["sub"]))
    out.append('  </div>')
    out.append('  <div class="theme-desc">%s</div>' % tm["desc"])
    for fn, cap in (tm.get("figures") or ([tm["figure"]] if tm.get("figure") else [])):
        alt = cap.replace("图 ", "").replace(" · ", "：", 1)
        out.append('  <figure class="figure-wide">')
        out.append('    <img src="assets/images/%s" alt="%s" width="1427" height="767" loading="lazy"' % (fn, esc(alt)))
        out.append('         data-figure="assets/images/%s" data-caption="%s">' % (fn, esc(cap)))
        out.append('    <figcaption>%s</figcaption>' % esc(cap))
        out.append('  </figure>')
    out.append('  <div class="paper-grid">')
    for p in items:
        win = "now" if p["inWindow"] else "pre"
        win_txt = "近三年窗口内" if p["inWindow"] else "奠基前置"
        out.append('    <article class="paper-card">')
        out.append('      <div class="pc-tags">')
        out.append('        <span class="pc-tag venue">%s</span>' % esc(p["venue"]))
        out.append('        <span class="pc-tag theme">%s</span>' % esc(p["themeZh"]))
        out.append('        <span class="pc-tag %s">%s</span>' % (win, win_txt))
        out.append('      </div>')
        out.append('      <h3>%s</h3>' % esc(p["title"]))
        out.append('      <div class="pc-zh">%s</div>' % esc(p["titleZh"]))
        out.append('      <div class="pc-id">arXiv:%s · %s · %s</div>' % (p["id"], p["published"], esc(authors_line(p["authors"]))))
        out.append('      <div class="pc-idea"><b>核心思想</b>%s</div>' % esc(p["coreIdea"]))
        out.append('      <div class="pc-inno-title">创新点</div>')
        out.append('      <ul class="pc-inno">')
        for i, iv in enumerate(p["innovation"], 1):
            out.append('        <li>%s</li>' % esc(iv))
        out.append('      </ul>')
        out.append('      <div class="pc-foot">')
        out.append('        <div class="pc-metric">📊 %s</div>' % esc(p["metrics"]))
        out.append('        <div class="pc-cite">✍️ %s</div>' % esc(p["whyCite"]))
        out.append('        <a class="pc-link" href="%s" target="_blank" rel="noopener">arXiv:%s 原文 ↗</a>' % (p["arxivUrl"], p["id"]))
        out.append('      </div>')
        out.append('    </article>')
    out.append('  </div>')
    out.append('</div>')
    out.append('')

sys.stdout.write("\n".join(out))
