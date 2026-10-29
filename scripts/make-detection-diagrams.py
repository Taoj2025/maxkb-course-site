"""
生成「目标检测」专题页的配图（object-detection.html 用）

风格对齐站点已有的课程配图（02/03/04/05/06/07 都是 matplotlib 画的）：
浅底 #FBFAFF、紫色标题、圆角卡片 + 细箭头、Microsoft YaHei。

布局全部基于「实测文本尺寸」计算，不靠手调坐标 —— 避免文字溢出卡片。

跑法：python scripts/make-detection-diagrams.py
输出：assets/images/08_ ~ 16_ 共 9 张 PNG
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib import font_manager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "images")

# ── 中文字体 ──
for cand in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"]:
    if os.path.exists(cand):
        font_manager.fontManager.addfont(cand)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=cand).get_name()
        break
plt.rcParams["axes.unicode_minus"] = False

# ── 配色（与既有配图一致）──
PURPLE = "#5B2EBF"
PURPLE_L = "#8B5CF6"
PURPLE_F = "#EDE9FE"
BLUE = "#3B82F6"
BLUE_L = "#DBEAFE"
TEAL = "#0D9488"
TEAL_L = "#CCFBF1"
GOLD = "#B8860B"
GOLD_F = "#F5DEB3"
ROSE = "#BE123C"
ROSE_L = "#FFE4E6"
SLATE = "#334155"
SLATE_L = "#E2E8F0"
GRAY = "#6B7280"
BG = "#FBFAFF"

LS = 1.5  # 统一行距


# ══════════════════════════════════════════════════════════════
# 文本尺寸实测（matplotlib renderer 直接量，避免溢出）
# ══════════════════════════════════════════════════════════════
def meas(fig, ax, text, fs, ls=LS, bold=False):
    """返回 (宽, 高)，单位为数据坐标"""
    t = ax.text(0, 0, text, fontsize=fs, linespacing=ls, va="top",
                fontweight="bold" if bold else "normal")
    r = fig.canvas.get_renderer()
    bb = t.get_window_extent(renderer=r).transformed(ax.transData.inverted())
    t.remove()
    return float(bb.width), float(bb.height)


_ADV = {}


def adv(fig, ax, fs, ls=LS):
    """行距（一个基线到下一个基线的距离，单位 y 坐标）"""
    key = (round(fs, 2), round(ls, 2))
    if key not in _ADV:
        s = "国Ag"
        _, h1 = meas(fig, ax, s, fs, ls)
        _, h2 = meas(fig, ax, s + "\n" + s, fs, ls)
        _ADV[key] = h2 - h1
    return _ADV[key]


def fitw(fig, ax, text, maxw, fs, ls=LS, bold=False):
    """字号自适应：保证文字宽度不超过 maxw"""
    w, _ = meas(fig, ax, text, fs, ls, bold)
    if w > maxw and w > 0:
        fs = max(6.5, fs * maxw / w)
    return fs


# ══════════════════════════════════════════════════════════════
# 绘图基元
# ══════════════════════════════════════════════════════════════
def new_fig(w=14.27, h=7.67):
    fig, ax = plt.subplots(figsize=(w, h), dpi=100)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def title(ax, main, sub=None, y=94):
    ax.text(50, y, main, ha="center", va="center",
            fontsize=27, color=PURPLE, fontweight="bold")
    if sub:
        ax.text(50, y - 8.5, sub, ha="center", va="center",
                fontsize=14, color=GRAY)


def card(ax, x, y, w, h, edge=PURPLE, fill="white", lw=2.4, r=1.6, z=2):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0,rounding_size=%.1f" % r,
        linewidth=lw, edgecolor=edge, facecolor=fill, zorder=z))


def box(ax, x, y, w, h, text, edge=PURPLE, fill=PURPLE_F, fs=15,
        bold=False, tcolor=None, r=1.6, tc_fs=None):
    card(ax, x, y, w, h, edge=edge, fill=fill, lw=2.2, r=r, z=2)
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=tc_fs or fs, color=tcolor or edge,
                fontweight="bold" if bold else "normal", zorder=3,
                linespacing=LS)


def arrow(ax, p0, p1, color=PURPLE, lw=2.2, style="-|>", ms=18, rad=0.0):
    ax.add_patch(FancyArrowPatch(
        p0, p1, arrowstyle=style, mutation_scale=ms, linewidth=lw,
        color=color, zorder=3,
        connectionstyle="arc3,rad=%.2f" % rad if rad else "arc3"))


def label(ax, x, y, text, fs=13, color=GRAY, bold=False, ha="center", va="center"):
    ax.text(x, y, text, ha=ha, va=va, fontsize=fs, color=color,
            fontweight="bold" if bold else "normal", zorder=3, linespacing=LS)


def stack(fig, ax, x, y_top, items, gap=0.7, ls=LS):
    """多行文本块：y_top 为顶部（va=top），逐行向下排；返回底部 y"""
    y = y_top
    for it in items:
        t = it["t"]
        fs = it["fs"]
        ax.text(x, y, t, ha=it.get("ha", "left"), va="top", fontsize=fs,
                color=it.get("c", SLATE),
                fontweight="bold" if it.get("b") else "normal",
                zorder=3, linespacing=ls)
        y -= adv(fig, ax, fs, ls) * (t.count("\n") + 1) + gap
    return y


def footer(ax, text, y=4.5, fs=12, color=GRAY):
    ax.text(50, y, text, ha="center", va="center", fontsize=fs, color=color)


def tag(ax, x, y, text, color=PURPLE, fs=12):
    ax.text(x, y, text, ha="center", va="center", fontsize=fs,
            color=color, fontweight="bold", zorder=4,
            bbox=dict(boxstyle="round,pad=0.32", fc="white", ec=color, lw=1.4))


def rule(ax, x0, x1, y, color=PURPLE, lw=1.1, alpha=.4):
    ax.plot([x0, x1], [y, y], color=color, linewidth=lw, alpha=alpha, zorder=3)


def save(fig, name):
    out = os.path.join(IMG, name)
    plt.savefig(out, dpi=100, facecolor=BG, bbox_inches=None)
    plt.close(fig)
    print("  ok", name, os.path.getsize(out), "bytes")


# ══════════════════════════════════════════════════════════════
# 08 · 检测器通用架构（Backbone / Neck / Head 解剖）
# ══════════════════════════════════════════════════════════════
def d08():
    fig, ax = new_fig()
    title(ax, "目标检测器 · 通用架构解剖",
          "任何检测器都是「特征提取 → 多尺度融合 → 预测头」三段式，差别在每一段的实现")

    box(ax, 2.5, 54, 11, 18, "输入图像\nW×H×3", edge=SLATE, fill=SLATE_L, fs=12, tc_fs=11.5)

    # ── Backbone ──
    card(ax, 17, 44, 20, 36, edge=PURPLE, fill=PURPLE_F)
    label(ax, 27, 76, "① Backbone 骨干", fs=12.5, color=PURPLE, bold=True)
    label(ax, 27, 70.5, "ResNet / Swin / VMamba", fs=10.5, color=SLATE)
    for i, (n, s) in enumerate([("C3", "stride 8"), ("C4", "stride 16"), ("C5", "stride 32")]):
        yy = 64 - i * 5.6
        rule(ax, 19.5, 34.5, yy + 2.3, PURPLE_L, 1.0, .5)
        label(ax, 27, yy, "%s   %s" % (n, s), fs=11, color=SLATE)

    # ── Neck ──
    card(ax, 41, 44, 20, 36, edge=BLUE, fill=BLUE_L)
    label(ax, 51, 76, "② Neck 特征融合", fs=12.5, color=BLUE, bold=True)
    label(ax, 51, 70.5, "FPN / PAN / CCFM", fs=10.5, color=SLATE)
    for i, (n, s) in enumerate([("P3", "小目标"), ("P4", "中目标"), ("P5", "大目标")]):
        yy = 64 - i * 5.6
        rule(ax, 43.5, 58.5, yy + 2.3, BLUE, 1.0, .5)
        label(ax, 51, yy, "%s   %s" % (n, s), fs=11, color=SLATE)

    # ── Head ──
    card(ax, 65, 44, 20, 36, edge=TEAL, fill=TEAL_L)
    label(ax, 75, 76, "③ Head 预测头", fs=12.5, color=TEAL, bold=True)
    label(ax, 75, 70.5, "分类 + 回归（两条路）", fs=10.5, color=SLATE)
    label(ax, 75, 64.5, "Anchor-based", fs=11, color=SLATE)
    label(ax, 75, 60, "RPN+RoI / Dense Head", fs=10, color=SLATE)
    label(ax, 75, 55, "Anchor-free", fs=11, color=SLATE)
    label(ax, 75, 50.5, "FCOS / DETR Query", fs=10, color=SLATE)

    box(ax, 89, 54, 9, 18, "输出\n框 + 类别\n+ 置信度", edge=ROSE, fill=ROSE_L, fs=11, tc_fs=10.5)

    arrow(ax, (13.5, 62), (17, 62))
    arrow(ax, (37, 62), (41, 62))
    arrow(ax, (61, 62), (65, 62))
    arrow(ax, (85, 62), (89, 62))

    # ── 训练 / 推理 ──
    card(ax, 5, 8, 43, 30, edge=PURPLE, fill="white")
    label(ax, 26.5, 33, "训练阶段 · 样本分配与损失", fs=12.5, color=PURPLE, bold=True)
    stack(fig, ax, 8, 28, [
        dict(t="两阶段：RPN → IoU 阈值匹配 → RoI 分类回归", fs=10.5),
        dict(t="一阶段：每个位置直接预测 → 与 GT 匹配", fs=10.5),
        dict(t="端到端：匈牙利匹配（一对一）+ 集合预测损失", fs=10.5),
    ])

    card(ax, 52, 8, 43, 30, edge=BLUE, fill="white")
    label(ax, 73.5, 33, "推理阶段 · 后处理", fs=12.5, color=BLUE, bold=True)
    stack(fig, ax, 55, 28, [
        dict(t="传统：NMS 按 IoU 抑制冗余框", fs=10.5),
        dict(t="NMS-free：直接输出最终框，无需后处理", fs=10.5),
        dict(t="端到端 DETR：查询即为答案，天然无冗余", fs=10.5),
    ])

    footer(ax, "近三年的演进，本质是在「③ 预测头」与「训练样本分配」两处动刀", y=4)
    save(fig, "08_检测器通用架构.png")


# ══════════════════════════════════════════════════════════════
# 09 · 三条技术路线对比
# ══════════════════════════════════════════════════════════════
def d09():
    fig, ax = new_fig()
    title(ax, "目标检测 · 三条技术路线",
          "两阶段精细、一阶段直接、端到端去 NMS —— 近三年所有新工作都落在这三条线上")

    cols = [
        dict(x=3, name="两阶段检测", en="Two-Stage", color=PURPLE, fill=PURPLE_F,
             parts=["Backbone", "RPN", "RoI Align", "分类 + 回归"],
             rep="Faster R-CNN / Cascade R-CNN",
             pro="优势：精度上限高，小目标强",
             con="短板：流程长、两段训练、推理慢"),
        dict(x=35, name="一阶段检测", en="One-Stage", color=BLUE, fill=BLUE_L,
             parts=["Backbone", "FPN", "Dense Head", "分类 + 回归"],
             rep="YOLOv5 / v8 / v9 / v10 / v12",
             pro="优势：端到端训练、速度快、易部署",
             con="短板：正负样本失衡，早期精度低"),
        dict(x=67, name="端到端检测", en="End-to-End DETR", color=TEAL, fill=TEAL_L,
             parts=["Backbone", "Encoder", "Decoder(Query)", "直接出框"],
             rep="DETR / DINO / RT-DETR / DEIM",
             pro="优势：无 NMS、无锚框、架构统一",
             con="短板：收敛慢、密集目标较弱"),
    ]

    for c in cols:
        x = c["x"]
        card(ax, x, 8, 30, 72, edge=c["color"], fill="white")
        card(ax, x, 70, 30, 10, edge=c["color"], fill=c["fill"], z=3)
        label(ax, x + 15, 76.5, c["name"], fs=15, color=c["color"], bold=True)
        label(ax, x + 15, 72.3, c["en"], fs=10.5, color=SLATE)

        yy = 66
        for i, p in enumerate(c["parts"]):
            box(ax, x + 4, yy - 5, 22, 5, p, edge=c["color"], fill=c["fill"],
                fs=11, tc_fs=11, r=1.0)
            if i < len(c["parts"]) - 1:
                arrow(ax, (x + 15, yy - 5.3), (x + 15, yy - 8.3), color=c["color"], lw=1.6, ms=13)
            yy -= 8.4

        label(ax, x + 15, 32, "代表工作", fs=10.5, color=GRAY, bold=True)
        label(ax, x + 15, 26.5, c["rep"], fs=11.5, color=c["color"], bold=True)
        rule(ax, x + 3, x + 27, 21.5, c["color"])
        label(ax, x + 3.5, 17.5, c["pro"], fs=10, color=SLATE, ha="left")
        label(ax, x + 3.5, 12.5, c["con"], fs=10, color=SLATE, ha="left")

    footer(ax, "趋势：两阶段被「一阶段 + 更好的样本分配」逼近；一阶段被「端到端」改造去 NMS；三条线互相吸收", y=3.5)
    save(fig, "09_三条技术路线对比.png")


# ══════════════════════════════════════════════════════════════
# 10 · DETR 端到端训练流程（含匈牙利匹配 + 去噪）
# ══════════════════════════════════════════════════════════════
def d10():
    fig, ax = new_fig()
    title(ax, "DETR 端到端检测 · 训练与推理原理",
          "把检测变成「集合预测」：一对一匹配替代 NMS，用匈牙利算法求全局最优")

    box(ax, 2, 61, 12, 17, "图像\n特征", edge=SLATE, fill=SLATE_L, fs=11, tc_fs=11)
    box(ax, 17, 59, 15, 19, "Transformer\nEncoder", edge=PURPLE, fill=PURPLE_F, fs=11, tc_fs=11)
    box(ax, 35, 59, 15, 19, "Decoder\nN 个 Query", edge=BLUE, fill=BLUE_L, fs=11, tc_fs=11)
    box(ax, 53, 59, 15, 19, "预测集合\n(框, 类别)", edge=TEAL, fill=TEAL_L, fs=11, tc_fs=11)
    arrow(ax, (14, 69.5), (17, 69.5))
    arrow(ax, (32, 69.5), (35, 69.5))
    arrow(ax, (50, 69.5), (53, 69.5))
    label(ax, 71.5, 75, "集合预测损失", fs=12, color=SLATE, bold=True, ha="left")
    stack(fig, ax, 71.5, 70, [
        dict(t="L_box  (L1 + GIoU)", fs=10.5, c=GRAY),
        dict(t="L_cls  (交叉熵)", fs=10.5, c=GRAY),
    ])

    # ① 匈牙利匹配
    card(ax, 2, 32, 37, 24, edge=GOLD, fill=GOLD_F)
    label(ax, 20.5, 51.5, "① 匈牙利匹配 · 一一对应", fs=12, color=GOLD, bold=True)
    stack(fig, ax, 5, 47, [
        dict(t="构造 N×M 代价矩阵 → 求最优排列", fs=10.5),
        dict(t="每个 GT 只被 1 个 Query 匹配", fs=10.5),
        dict(t="其余 Query 全部计为无目标", fs=10.5),
    ])

    # 代价矩阵示意
    for i in range(4):
        for j in range(4):
            on = (i == j)
            ax.add_patch(Rectangle((43 + j * 4.3, 45 - i * 2.4), 3.8, 2.0,
                                   linewidth=0.9, edgecolor=GOLD if on else SLATE_L,
                                   facecolor=GOLD if on else "white", zorder=3))
    label(ax, 51.5, 52, "代价矩阵 (Query × GT)", fs=10.5, color=GRAY)
    label(ax, 51.5, 35.5, "全局最优而非贪心 IoU", fs=10.5, color=GOLD, bold=True)

    # ② 去噪训练
    card(ax, 63, 32, 35, 24, edge=PURPLE_L, fill=PURPLE_F)
    label(ax, 80.5, 51.5, "② 去噪训练 DINO / CDN", fs=12, color=PURPLE, bold=True)
    stack(fig, ax, 66, 47, [
        dict(t="给 GT 框加随机噪声，作为额外", fs=10.5),
        dict(t="正样本 Query 送进 Decoder 一起训练", fs=10.5),
        dict(t="模型只需「去噪还原」→ 收敛快数倍", fs=10.5),
    ])

    # 传统 vs 端到端
    card(ax, 2, 6, 46, 23, edge=SLATE, fill="white")
    label(ax, 25, 25, "传统检测：先出候选，再筛选", fs=11.5, color=SLATE, bold=True)
    stack(fig, ax, 5, 21, [
        dict(t="几百个候选框 → 按 IoU 阈值保留 → NMS 抑制", fs=10.5, c=GRAY),
        dict(t="问题：候选与 GT 的分配是启发式的（贪心 IoU）", fs=10.5, c=ROSE),
        dict(t="不是全局最优，且训练与推理目标不一致", fs=10.5, c=ROSE),
    ])

    card(ax, 51, 6, 47, 23, edge=TEAL, fill="white")
    label(ax, 74.5, 25, "端到端检测：直接预测最终结果", fs=11.5, color=TEAL, bold=True)
    stack(fig, ax, 54, 21, [
        dict(t="N 个 Query 一一对应 M 个 GT，没有冗余框", fs=10.5, c=GRAY),
        dict(t="收益：训练目标与推理目标一致，可端到端优化", fs=10.5, c=GRAY),
        dict(t="代价：早期收敛慢、小目标弱 → 后续工作补上", fs=10.5, c=GRAY),
    ])

    footer(ax, "去噪训练（DINO 提出）是近三年所有 DETR 系工作提速的共同前提", y=2.5, fs=11.5)
    save(fig, "10_DETR端到端训练.png")


# ══════════════════════════════════════════════════════════════
# 11 · DINO / DEIM / D-FINE 三种改进对比
# ══════════════════════════════════════════════════════════════
def d11():
    fig, ax = new_fig()
    title(ax, "DETR 系三大关键改进 · DINO / DEIM / D-FINE",
          "近三年 DETR 的性能跃升，来自「匹配方式」与「回归形式」两条线上的持续改良")

    items = [
        dict(x=3, name="DINO", sub="ICLR 2023 · arXiv:2203.03605", color=PURPLE, fill=PURPLE_F,
             before="标准 DETR：Query 与 GT 一对一匹配",
             after="① 去噪训练 CDN\n② 混合查询选择（内容 + 位置）\n③ Look-Forward-Twice\n④ 解码器额外精修层",
             gain="AP 42.3 → 49.0（R50, 12 epoch）",
             note="收敛从 500 epoch 拉到 12 epoch"),
        dict(x=35, name="DEIM", sub="2024-12 · arXiv:2412.04234", color=BLUE, fill=BLUE_L,
             before="DINO：每个 GT 只匹配 1 个 Query",
             after="① 密集一对一匹配 Dense O2O\n② 每个 GT 取 Top-K 个候选 Query\n③ 匹配性感知损失 MAL",
             gain="同 12 epoch 下 AP 50.6",
             note="更多 Query 拿到正监督，收敛再快一档"),
        dict(x=67, name="D-FINE", sub="2024-10 · arXiv:2410.13842", color=TEAL, fill=TEAL_L,
             before="传统回归：直接预测一个框坐标",
             after="① 回归重新定义为\n　细粒度分布细化 FDR\n② 预测距离分布而非单点\n③ 全局分布细化 GDR + 迭代精修",
             gain="R50 AP 54.3 / L AP 64.6",
             note="分布式回归在定位精度上碾压 L1"),
    ]

    for it in items:
        x = it["x"]
        card(ax, x, 8, 30, 72, edge=it["color"], fill="white")
        card(ax, x, 70, 30, 10, edge=it["color"], fill=it["fill"], z=3)
        label(ax, x + 15, 76.5, it["name"], fs=17, color=it["color"], bold=True)
        label(ax, x + 15, 72.3, it["sub"], fs=10, color=SLATE)

        label(ax, x + 15, 65, "改进前", fs=11, color=GRAY, bold=True)
        label(ax, x + 15, 60, it["before"], fs=10.5, color=SLATE)
        arrow(ax, (x + 15, 57), (x + 15, 53), color=it["color"], lw=2.0, ms=16)

        label(ax, x + 15, 49, "改进后", fs=11, color=GRAY, bold=True)
        stack(fig, ax, x + 15, 45, [
            dict(t=it["after"], fs=11, c=it["color"], b=True, ha="center"),
        ], gap=0.5)

        rule(ax, x + 3, x + 27, 25, it["color"])
        label(ax, x + 15, 20.5, it["gain"], fs=11.5, color=it["color"], bold=True)
        label(ax, x + 15, 14.5, it["note"], fs=10.5, color=GRAY)

    footer(ax, "写文章时的叙事线：收敛慢 → 密集匹配（DEIM）→ 回归形式（D-FINE），两条线彼此正交、可叠加", y=4)
    save(fig, "11_DETR三大改进对比.png")


# ══════════════════════════════════════════════════════════════
# 12 · RT-DETR 混合编码器
# ══════════════════════════════════════════════════════════════
def d12():
    fig, ax = new_fig()
    title(ax, "RT-DETR · 混合编码器与查询选择",
          "CVPR 2024 · arXiv:2304.08069 —— 让 DETR 跑进实时区间")

    card(ax, 2, 54, 15, 24, edge=SLATE, fill=SLATE_L)
    label(ax, 9.5, 74, "Backbone", fs=12, color=SLATE, bold=True)
    for i, (n, s) in enumerate([("S3", "1/8"), ("S4", "1/16"), ("S5", "1/32")]):
        label(ax, 9.5, 67 - i * 4.6, "%s   %s" % (n, s), fs=11, color=SLATE)

    box(ax, 21, 61, 16, 15, "AIFI\n同尺度交互\n仅作用于 S3", edge=PURPLE, fill=PURPLE_F, fs=11, tc_fs=11)
    box(ax, 41, 58, 17, 20, "CCFM\n跨尺度融合\n简化 FPN/PAN", edge=BLUE, fill=BLUE_L, fs=11, tc_fs=11)
    card(ax, 62, 52, 17, 26, edge=GOLD, fill=GOLD_F)
    label(ax, 70.5, 74, "查询选择", fs=12, color=GOLD, bold=True)
    stack(fig, ax, 64.5, 69.5, [
        dict(t="不确定性最小", fs=10),
        dict(t="取编码器输出中", fs=10),
        dict(t="置信度最高的 K 个", fs=10),
        dict(t="作为位置查询", fs=10),
    ], gap=0.2)
    box(ax, 83, 58, 15, 20, "Decoder\n逐层精修\nNMS-free", edge=TEAL, fill=TEAL_L, fs=11, tc_fs=11)

    arrow(ax, (17, 66), (21, 66))
    arrow(ax, (37, 66), (41, 66))
    arrow(ax, (58, 66), (62, 66))
    arrow(ax, (79, 66), (83, 66))
    label(ax, 9.5, 81, "多尺度特征", fs=10, color=GRAY)

    cards = [
        ("① AIFI 同尺度交互", "只在最高分辨率的 S3 上做一次\nintra-scale 注意力，其余层保持\n卷积处理 —— 兼顾精度与速度", PURPLE, PURPLE_F),
        ("② CCFM 跨尺度融合", "用极简的自顶向下融合替换\nFPN/PAN 的重复卷积，融合后的\n多尺度特征直接给查询选择用", BLUE, BLUE_L),
        ("③ 不确定性最小查询", "按分类 / 定位置信度综合打分，\n只保留最可靠的 K 个查询进入\nDecoder —— 少而精的初始化", GOLD, GOLD_F),
    ]
    for i, (h, b, c, f) in enumerate(cards):
        x = 4 + i * 32
        card(ax, x, 22, 28, 28, edge=c, fill=f, lw=2.0)
        label(ax, x + 14, 45, h, fs=12.5, color=c, bold=True)
        stack(fig, ax, x + 14, 39.5, [
            dict(t=b, fs=11, c=SLATE, ha="center"),
        ], gap=0.3)

    footer(ax, "效果：COCO 上 T4 GPU 108 FPS 达到 53.1 AP —— 首次让 DETR 进入实时可用区间", y=15)
    footer(ax, "写论文的价值点：把「实时」从「换 backbone」变成「架构级设计」的问题", y=9, fs=11)
    save(fig, "12_RT-DETR混合编码器.png")


# ══════════════════════════════════════════════════════════════
# 13 · YOLO 系实时检测演进
# ══════════════════════════════════════════════════════════════
def d13():
    fig, ax = new_fig()
    title(ax, "YOLO 系 · 近三年三个关键版本",
          "YOLOv9 解决梯度信息断裂 · YOLOv10 去掉 NMS · YOLOv12 把注意力做便宜")

    items = [
        dict(x=3, name="YOLOv9", ver="2024-02 · arXiv:2402.13616", color=PURPLE, fill=PURPLE_F,
             pts=["PGI 可编程梯度信息",
                  "骨干加辅助分支 A2 / B2",
                  "把输入层梯度信息引回浅层",
                  "GELAN 通用高效层聚合 neck"],
             tagk="训练侧", tagd="解决深层监督失效"),
        dict(x=35, name="YOLOv10", ver="2024-05 · arXiv:2405.14458", color=BLUE, fill=BLUE_L,
             pts=["一致性双重标签分配",
                  "训练时 1:1 + 1:N 双分支",
                  "推理时只保留 1:1 分支",
                  "完全 NMS-free 端到端"],
             tagk="推理侧", tagd="消除后处理延迟"),
        dict(x=67, name="YOLOv12", ver="2025-02 · arXiv:2502.12524", color=TEAL, fill=TEAL_L,
             pts=["以注意力为中心的架构",
                  "区域注意力 A2 + 块注意力 B2",
                  "FlashAttention 降低开销",
                  "轻量二维位置编码 PosE"],
             tagk="架构侧", tagd="精度与延迟再平衡"),
    ]

    for it in items:
        x = it["x"]
        card(ax, x, 16, 30, 64, edge=it["color"], fill="white")
        card(ax, x, 68, 30, 12, edge=it["color"], fill=it["fill"], z=3)
        label(ax, x + 15, 75.5, it["name"], fs=18, color=it["color"], bold=True)
        label(ax, x + 15, 70.5, it["ver"], fs=10.5, color=SLATE)

        yy = 62
        for p in it["pts"]:
            label(ax, x + 3, yy, "· " + p, fs=11.5, color=SLATE, ha="left")
            yy -= 6.6

        tag(ax, x + 15, 31, it["tagk"], color=it["color"])
        label(ax, x + 15, 23, it["tagd"], fs=12, color=it["color"], bold=True)

    footer(ax, "共同主线：把「训练与推理不一致」和「后处理开销」这两个老问题逐个消掉 —— 三者互补而非互斥", y=10)
    footer(ax, "工程视角：Ultralytics 系列代码高度统一，v9 / v10 / v12 的差异集中在 loss 与 head，改造成本低", y=5)
    save(fig, "13_YOLO实时检测演进.png")


# ══════════════════════════════════════════════════════════════
# 14 · 开放词汇检测三种范式
# ══════════════════════════════════════════════════════════════
def d14():
    fig, ax = new_fig()
    title(ax, "开放词汇检测 · 三种主流范式",
          "从闭集 80 类到「任意文本描述的类别」—— 这一步改写了检测器的任务定义")

    rows = [
        dict(y=62, name="Grounding DINO", ver="2023-03 · arXiv:2303.05499", color=PURPLE, fill=PURPLE_F,
             chain=["文本提示", "BERT 编码", "语言-图像\n自注意力", "跨模态\nDecoder", "文本框"]),
        dict(y=40, name="OWLv2", ver="2023-06 · arXiv:2306.09683", color=BLUE, fill=BLUE_L,
             chain=["图像", "ViT 编码器", "类无关\n候选框", "CLIP 特征", "文本匹配\n打分"]),
        dict(y=18, name="YOLO-World", ver="2024-01 · arXiv:2401.17270", color=TEAL, fill=TEAL_L,
             chain=["文本提示", "CLIP 文本\n编码器", "重参数化\n文本 → 头", "YOLO\n检测头", "实时输出"]),
    ]

    for r in rows:
        y = r["y"]
        card(ax, 2, y, 20, 18, edge=r["color"], fill=r["fill"], lw=2.2, z=3)
        label(ax, 12, y + 12, r["name"], fs=14, color=r["color"], bold=True)
        label(ax, 12, y + 6, r["ver"], fs=9.5, color=SLATE)

        n = len(r["chain"])
        bw, gap = 13.2, 2.0
        x0 = 25
        for i, p in enumerate(r["chain"]):
            x = x0 + i * (bw + gap)
            box(ax, x, y + 4, bw, 10, p, edge=r["color"], fill="white", fs=10.5, tc_fs=10.5, r=1.0)
            if i < n - 1:
                arrow(ax, (x + bw + 0.3, y + 9), (x + bw + gap - 0.3, y + 9), color=r["color"], lw=1.8, ms=14)

    card(ax, 2, 4, 96, 10, edge=SLATE, fill="white")
    label(ax, 50, 11, "共同瓶颈：开放词汇带来长尾难题 —— 训练集里没见过的类别，如何可靠地定位并识别？",
          fs=12.5, color=SLATE, bold=True)
    label(ax, 50, 6.5, "2024 年之后的主流做法是「检测器 + 视觉语言模型」双组件协作，而非单一模型包打天下",
          fs=11, color=GRAY)
    save(fig, "14_开放词汇检测三范式.png")


# ══════════════════════════════════════════════════════════════
# 15 · 小目标检测：难点与解法
# ══════════════════════════════════════════════════════════════
def d15():
    fig, ax = new_fig()
    title(ax, "小目标检测 · 难点解剖与主流解法",
          "目标小于 32×32 像素时，检测器丢掉的不只是细节，还有「位置先验」")

    # ── 问题 ──
    card(ax, 2, 30, 31, 50, edge=SLATE, fill="white")
    label(ax, 17.5, 75, "问题：特征逐层丢失", fs=12.5, color=SLATE, bold=True)
    for i, (n, s, small) in enumerate([("P3", "stride 8", True), ("P4", "stride 16", False), ("P5", "stride 32", False)]):
        yy = 66 - i * 11
        box(ax, 4.5, yy - 3.5, 10, 7, n, edge=ROSE if small else BLUE,
            fill=ROSE_L if small else BLUE_L, fs=12, tc_fs=12, r=1.0)
        label(ax, 17, yy + 1.6, s, fs=11, color=SLATE, ha="left")
        label(ax, 17, yy - 2.4, "小目标仅剩 %d 像素" % (32 // (8 * (i + 1))) if small else "语义已足够",
              fs=10, color=ROSE if small else GRAY, ha="left")
    label(ax, 17.5, 35, "32×32 的目标在 P3 上只剩 4×4", fs=11, color=ROSE, bold=True)

    # ── 解法 ──
    card(ax, 35, 30, 31, 50, edge=PURPLE, fill="white")
    label(ax, 50.5, 75, "解法：四条主线", fs=12.5, color=PURPLE, bold=True)
    sols = [
        ("特征融合", "FPN / PAN 自顶向下融合，把高层语义送到高分辨率层", PURPLE, PURPLE_F),
        ("提高分辨率", "切片推理 SAHI / TTA，大图切块分别检测再合并", BLUE, BLUE_L),
        ("位置先验", "Anchor-free + 可学习位置编码，缓解正样本稀缺", TEAL, TEAL_L),
        ("注意力", "Swin / VMamba 层次化注意力，或专用小目标头", GOLD, GOLD_F),
    ]
    for i, (h, b, c, f) in enumerate(sols):
        yy = 65 - i * 9.4
        card(ax, 37, yy - 4.1, 27, 8.2, edge=c, fill=f, lw=1.6, r=1.0, z=3)
        label(ax, 50.5, yy + 1.8, h, fs=11.5, color=c, bold=True)
        bfs = fitw(fig, ax, b, 24, 10)
        stack(fig, ax, 50.5, yy - 0.4, [dict(t=b, fs=bfs, c=SLATE, ha="center")], gap=0)

    # ── 数据与评测 ──
    card(ax, 68, 30, 30, 50, edge=GOLD, fill="white")
    label(ax, 83, 75, "数据与评测", fs=12.5, color=GOLD, bold=True)
    label(ax, 83, 70, "专用数据集", fs=11, color=GOLD, bold=True)
    stack(fig, ax, 70, 65.5, [
        dict(t="VisDrone / UAVDT（无人机）", fs=9.5),
        dict(t="Objects365 / CrowdHuman（密集）", fs=9.5),
        dict(t="DOTA（遥感旋转框）", fs=9.5),
    ], gap=0.1)
    label(ax, 83, 52.5, "评测指标", fs=11, color=GOLD, bold=True)
    stack(fig, ax, 70, 48, [
        dict(t="AP_s（小目标）单独统计", fs=9.5),
        dict(t="AP50 / AP75 更严格", fs=9.5),
    ], gap=0.1)
    stack(fig, ax, 70, 38.5, [
        dict(t="论文写作提示：单报 AP 会被质疑，", fs=9.5, c=ROSE),
        dict(t="应同时给出 AP_s 与推理速度", fs=9.5, c=ROSE),
    ], gap=0.1)

    # ── 收尾 ──
    card(ax, 2, 4, 96, 22, edge=PURPLE, fill=PURPLE_F)
    label(ax, 50, 22, "为什么小目标仍是活跃的研究方向？", fs=13, color=PURPLE, bold=True)
    stack(fig, ax, 50, 17.5, [
        dict(t="因为它不是一个「调参问题」，而是一个「特征分辨率与语义粒度的根本矛盾」——", fs=10.5, c=SLATE, ha="center"),
        dict(t="提高分辨率会显著增加计算量，语义太弱又无法可靠分类。这个矛盾至今没有被彻底解决，", fs=10.5, c=SLATE, ha="center"),
        dict(t="正好构成一个可发论文的持续性议题。", fs=10.5, c=SLATE, ha="center"),
    ], gap=0.1)
    save(fig, "15_小目标检测难点.png")


# ══════════════════════════════════════════════════════════════
# 16 · 近三年研究脉络（四条主线）
# ══════════════════════════════════════════════════════════════
def d16():
    fig, ax = new_fig()
    title(ax, "近三年目标检测 · 四条研究主线",
          "2023.10 —— 2026.10：端到端、实时化、开放词汇、基础模型并行推进")

    lanes = [
        dict(x=2, name="端到端 DETR 系", color=PURPLE, fill=PURPLE_F,
             papers=[("DETR / DINO", "2022.03 · 2203.03605 · 前置工作"),
                     ("D-FINE", "2024.10 · 2410.13842 · 分布式回归"),
                     ("DEIM", "2024.12 · 2412.04234 · 密集一对一匹配"),
                     ("DETR 系后续", "2025–2026 · 匹配与回归继续改良")]),
        dict(x=27, name="实时检测", color=BLUE, fill=BLUE_L,
             papers=[("RT-DETR", "2023.04 · 2304.08069 · 混合编码器进入实时"),
                     ("YOLOv9", "2024.02 · 2402.13616 · PGI 梯度信息"),
                     ("YOLOv10", "2024.05 · 2405.14458 · NMS-free 端到端"),
                     ("YOLOv12", "2025.02 · 2502.12524 · 注意力中心架构")]),
        dict(x=52, name="开放词汇检测", color=TEAL, fill=TEAL_L,
             papers=[("Grounding DINO", "2023.03 · 2303.05499 · 语言注入 DETR"),
                     ("OWLv2", "2023.06 · 2306.09683 · 先检测再分类"),
                     ("YOLO-World", "2024.01 · 2401.17270 · 实时开放词汇"),
                     ("检测器 + VLM", "2025–2026 · 双组件分工的新范式")]),
        dict(x=77, name="视觉基础模型", color=GOLD, fill=GOLD_F,
             papers=[("Florence-2", "2023.11 · 2311.06242 · 统一多任务 VLM"),
                     ("VMamba", "2024.01 · 2401.10166 · SSM 骨干"),
                     ("SAM 2", "2024.08 · 2408.00714 · 视频可提示分割"),
                     ("DINOv3", "2025.08 · 2508.10104 · 自监督基础模型")]),
    ]

    for lane in lanes:
        x = lane["x"]
        card(ax, x, 22, 21, 58, edge=lane["color"], fill="white", lw=2.2)
        card(ax, x, 70, 21, 10, edge=lane["color"], fill=lane["fill"], lw=2.2, z=3)
        label(ax, x + 10.5, 75, lane["name"], fs=11.5, color=lane["color"], bold=True)

        yy = 65
        for name, meta in lane["papers"]:
            label(ax, x + 2.5, yy, name, fs=11, color=lane["color"], bold=True, ha="left")
            mfs = fitw(fig, ax, meta, 16, 8.5)
            label(ax, x + 2.5, yy - 4.4, meta, fs=mfs, color=SLATE, ha="left")
            yy -= 9.6

    card(ax, 2, 4, 96, 15, edge=SLATE, fill="white")
    label(ax, 50, 15.5, "四条主线的交汇点", fs=12.5, color=SLATE, bold=True)
    label(ax, 50, 9.5, "端到端解决了「怎么输出」→ 实时化解决了「多快」→ 开放词汇解决了「认什么」→ 基础模型解决了「从哪学」",
          fs=10.5, color=GRAY)
    save(fig, "16_目标检测研究脉络.png")


if __name__ == "__main__":
    os.makedirs(IMG, exist_ok=True)
    print("生成目标检测专题配图：")
    for fn in (d08, d09, d10, d11, d12, d13, d14, d15, d16):
        fn()
    print("完成。")
