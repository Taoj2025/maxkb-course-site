"""
生成「深度学习课程体系」配图（首页 DL 课程入口卡用）

风格对齐已有的 6 张课程配图（02/03/04/05/06 都是 matplotlib 画的）：
浅底、紫色标题、圆角卡片、箭头连接。

跑法：python scripts/make-dl-diagram.py
输出：assets/images/07_深度学习课程体系.png（1427×767）
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import font_manager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "images", "07_深度学习课程体系.png")

# ── 中文字体 ──
for cand in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"]:
    if os.path.exists(cand):
        font_manager.fontManager.addfont(cand)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=cand).get_name()
        break
plt.rcParams["axes.unicode_minus"] = False

PURPLE = "#5B2EBF"
PURPLE_L = "#8B5CF6"
BLUE = "#3B82F6"
BLUE_L = "#DBEAFE"
GOLD = "#B8860B"
GOLD_L = "#F5DEB3"
GRAY = "#334155"
GRAY_L = "#E2E8F0"
BG = "#FBFAFF"

MODULES = [
    ("CNN", "卷积神经网络", ["图像分类 / 目标检测", "卷积核 · 池化 · 特征图", "实验 1-2"], PURPLE, "#DDD6FE"),
    ("RNN", "循环神经网络", ["序列建模 / 时序预测", "LSTM · GRU · 梯度消失", "实验 3-4"], PURPLE_L, "#EDE9FE"),
    ("Transformer", "注意力机制", ["BERT · GPT · 大模型", "自注意力 · 位置编码", "实验 5-6"], BLUE, BLUE_L),
    ("GAN", "生成对抗网络", ["图像生成 / 风格迁移", "判别器 · 生成器 · 对抗训练", "实验 7"], GOLD, GOLD_L),
]

fig, ax = plt.subplots(figsize=(14.27, 7.67), dpi=100)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")

# ── 标题 ──
ax.text(50, 93, "深度学习课程体系 · SKC5053", ha="center", va="center",
        fontsize=30, color=PURPLE, fontweight="bold")
ax.text(50, 86.5, "从原理推导到工业级实战 · 9 章系统讲解 · 7 大实验 · 54 学时",
        ha="center", va="center", fontsize=16, color="#6B7280")

# ── 4 个模块卡片 ──
W, H = 21, 42
GAP = 4.0
X0 = (100 - (W * 4 + GAP * 3)) / 2
Y0 = 30

for i, (name, cn, bullets, stroke, fill) in enumerate(MODULES):
    x = X0 + i * (W + GAP)
    box = FancyBboxPatch(
        (x, Y0), W, H,
        boxstyle="round,pad=0,rounding_size=1.6",
        linewidth=2.4, edgecolor=stroke, facecolor=fill, zorder=2,
    )
    ax.add_patch(box)

    ax.text(x + W / 2, Y0 + H - 6.2, name, ha="center", va="center",
            fontsize=21, color=stroke, fontweight="bold", zorder=3)
    ax.text(x + W / 2, Y0 + H - 11.0, cn, ha="center", va="center",
            fontsize=14, color=GRAY, zorder=3)

    # 分隔线
    ax.plot([x + 3, x + W - 3], [Y0 + H - 14.2, Y0 + H - 14.2],
            color=stroke, linewidth=1.2, alpha=0.45, zorder=3)

    for j, b in enumerate(bullets):
        ax.text(x + W / 2, Y0 + H - 19.5 - j * 6.2, b, ha="center", va="center",
                fontsize=13, color="#374151", zorder=3)

    # 序号徽标
    ax.text(x + 2.8, Y0 + H - 2.8, "0%d" % (i + 1), ha="center", va="center",
            fontsize=13, color=stroke, fontweight="bold", zorder=3)

    # 箭头
    if i < len(MODULES) - 1:
        ax.add_patch(FancyArrowPatch(
            (x + W + 0.4, Y0 + H / 2), (x + W + GAP - 0.4, Y0 + H / 2),
            arrowstyle="-|>", mutation_scale=22, linewidth=2.4,
            color=PURPLE, zorder=3,
        ))

# ── 底部：能力沉淀 ──
base = FancyBboxPatch(
    (X0, 14), W * 4 + GAP * 3, 10,
    boxstyle="round,pad=0,rounding_size=1.6",
    linewidth=2.0, edgecolor=PURPLE, facecolor="#F3EEFF", zorder=2,
)
ax.add_patch(base)
ax.text(X0 + (W * 4 + GAP * 3) / 2, 19,
        "能力沉淀：模型选型 → 数据处理 → 训练调优 → 推理部署 → 上线监控（A10 GPU 实验环境）",
        ha="center", va="center", fontsize=15, color=PURPLE, fontweight="bold", zorder=3)

# ── 底部说明 ──
ax.text(50, 6.5,
        "面向 AI 工程师的完整链路 · 代码全部可运行 · 配套 7 份实验手册与数据集",
        ha="center", va="center", fontsize=14, color="#6B7280")

plt.tight_layout()
plt.savefig(OUT, dpi=100, facecolor=BG)
print("已生成:", OUT, os.path.getsize(OUT), "bytes")
