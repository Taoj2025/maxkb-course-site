"""把 arXiv 抓取的元数据 + 中文精读批注合并成 data/object-detection-papers.json
跑法：python scripts/build-papers-json.py
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

META = json.load(io.open(os.path.join(DATA, "arxiv-detection-meta.json"), encoding="utf-8"))
meta_by_id = {}
for m in META:
    base = m["id"].split("v")[0]
    meta_by_id[base] = m

RECENT = json.load(io.open(os.path.join(DATA, "arxiv-detection-recent.json"), encoding="utf-8"))
for m in RECENT:
    meta_by_id.setdefault(m["id"], dict(
        id=m["id"], title=m["title"], published=m["published"], updated=m["updated"],
        authors=m["authors"], abstract=m["abstract"], cats=[]))

# theme: end2end / realtime / ovod / foundation / backbone
ANNOT = {
"2203.03605": dict(
    theme="end2end", venue="ICLR 2023", in_window=False,
    titleZh="DINO：带改进去噪锚框的端到端目标检测 DETR",
    coreIdea="把 DETR 的集合预测与去噪训练结合——给 GT 框加噪构造额外的正样本 Query，让 Decoder 同时学习「去噪还原」，把收敛所需的 500 epoch 压到 12 epoch。",
    innovation=[
        "引入对比去噪 CDN：给 GT 框加随机噪声，生成额外正样本 Query",
        "混合查询选择：把编码器的内容特征与位置锚点拼接起来选初始 Query",
        "Look-Forward-Twice：在分支之间传递梯度，稳定深层监督",
        "解码器额外精修层：逐层提升框的定位精度",
    ],
    metrics="COCO AP 42.3 → 49.0（ResNet-50，12 epoch）",
    whyCite="凡是要写「DETR 收敛慢」或「去噪训练」，这一篇是必引的前置工作，也是 DEIM / D-FINE 等后续改进的共同前提。"),
"2211.12860": dict(
    theme="end2end", venue="ICCV 2023", in_window=False,
    titleZh="协同混合分配训练的 DETR（Co-DETR）",
    coreIdea="指出 DETR 的「一对一匹配」导致正样本过于稀疏，改为在多个辅助检测头上做混合分配（一对一 + 一对多）协同训练，最后只保留主头的输出做推理。",
    innovation=[
        "协同混合分配训练：多个辅助头采用不同的正负样本分配策略",
        "正样本集合在辅助头之间共享，互相「借」监督信号",
        "推理时只保留一对一主头，完整保留 NMS-free 特性",
    ],
    metrics="COCO AP 51.0 级别，显著加速收敛",
    whyCite="讨论「正样本稀疏」「一对一匹配的信息瓶颈」时引用；与 DEIM 的 Dense O2O 是同期但独立的两种解法。"),
"2211.09788": dict(
    theme="end2end", venue="ICCV 2023 (Oral)", in_window=False,
    titleZh="DiffusionDet：用扩散模型做目标检测",
    coreIdea="把检测重述为「从带噪框集合到真实框集合」的扩散去噪过程——以随机初始化的框作为扩散起点，用迭代去噪逐步精修出最终检测结果，天然不需要 NMS。",
    innovation=[
        "首次把扩散模型的加噪 / 去噪范式引入目标检测",
        "随机框作为扩散起点，等价于隐式建模整个检测结果的分布",
        "去噪过程中逐级精修框坐标与类别，天然免 NMS",
    ],
    metrics="COCO AP 46.4（L 级骨干，RefineNet）",
    whyCite="讲「集合预测的另一种范式」或「扩散模型做感知任务」时引用；2024 年之后扩散式检测大量跟进，是一条活的支线。"),
"2304.07193": dict(
    theme="foundation", venue="TMLR 2024", in_window=False,
    titleZh="DINOv2：无监督学习鲁棒视觉特征",
    coreIdea="用自蒸馏配合自监督掩码策略，让学生在无标签数据上学会与教师一致的表征，把自监督预训练从「为分类服务」推进到「提供通用视觉特征」。",
    innovation=[
        "自蒸馏 + 自监督掩码的组合，规避跨样本蒸馏的不稳定",
        "特征自举（居中 + 锐化）防止表示坍塌",
        "海量无标签数据 + 多套预训练策略，特征可直接线性探测",
    ],
    metrics="冻结骨干在 COCO 检测上带来可观提升；线性探测优于同期有监督模型",
    whyCite="讨论「骨干网络怎么选」「自监督预训练值不值」时引用；也是 DETR 系列最常换的骨干来源。"),
"2304.08069": dict(
    theme="realtime", venue="CVPR 2024", in_window=False,
    titleZh="DETRs 在实时目标检测上击败 YOLO（RT-DETR）",
    coreIdea="认为 DETR 慢的根源在编码器冗余计算与查询初始化质量，于是用高效混合编码器压缩计算量，并用「不确定性最小」的查询选择取代传统查询初始化。",
    innovation=[
        "AIFI：只在最高分辨率的 S3 上做一次同尺度注意力，其余层保持卷积",
        "CCFM：以极简的自顶向下融合替代 FPN/PAN 的重复卷积",
        "不确定性最小查询选择：按分类 / 定位置信度筛出最可靠的 K 个查询",
        "推理全程 NMS-free，可直接导出为部署模型",
    ],
    metrics="COCO 上 T4 GPU 108 FPS 达到 53.1 AP；TensorRT FP16 达 217 FPS",
    whyCite="讨论「端到端检测器如何实时化」或「混合编码器」时引用；是把 DETR 推进到工程可用区间的代表作。"),
"2303.05499": dict(
    theme="ovod", venue="ECCV 2024", in_window=False,
    titleZh="Grounding DINO：把 DINO 与接地预训练结合用于开放集检测",
    coreIdea="在 DETR 的图像分支与文本分支之间加入跨模态自注意力，让文本与图像特征在 Encoder 阶段就充分交互，模型因此理解的是「文本框」而不只是类别名。",
    innovation=[
        "图像—文本跨模态自注意力，取代早期「先检测再分类」的后融合",
        "逐阶段文本—图像特征融合 + 语言引导的框查询选择",
        "引入大规模接地预训练数据，大幅提升开放集泛化",
        "输出与文本对齐的框，可直接交给 SAM 等下游模型",
    ],
    metrics="COCO 51.3 AP；ODinW-35 / LVIS 零样本约 35 AP 量级",
    whyCite="开放词汇检测的必引工作；写「检测器 + 视觉语言模型协同」范式时的起点。"),
"2306.09683": dict(
    theme="ovod", venue="ECCV 2024", in_window=False,
    titleZh="扩展开放词汇目标检测的规模（OWLv2）",
    coreIdea="把开放词汇检测拆成「类无关候选框 + 文本对齐分类」两步，并用大规模图文预训练与自训练蒸馏，把 OWL 从 ViT-B/32 扩展到 ViT-H/14 规模。",
    innovation=[
        "类无关候选框 + CLIP 式文本匹配的解耦架构",
        "37 亿图文对的大规模图文预训练，提升细粒度对齐",
        "自训练 + 蒸馏挖掘伪标签，弥补开放词汇标注稀缺",
        "规模化收益的系统性验证（更大骨干 + 更高分辨率）",
    ],
    metrics="LVIS 零样本 17.1 AP（ViT-H/14），较 OWL v1 提升约 9 AP",
    whyCite="与 Grounding DINO 并列的两大开放词汇路线（先分类 vs 深度融合）之一，写对比时通常成对引用。"),
"2311.06242": dict(
    theme="foundation", venue="CVPR 2024", in_window=False,
    titleZh="Florence-2：用统一表示处理多种视觉任务",
    coreIdea="用一个序列到序列模型统一指代表达、检测、描述、密集标注四类任务，把不同任务都变成「统一 prompt token 输入 + 文本生成输出」。",
    innovation=[
        "统一的 prompt-token 输入接口与序列生成输出",
        "多任务混合训练，任务之间互相增益",
        "构建 FLD-5B 大规模数据集（54 亿自动标注样本）",
        "单模型零样本即可完成开放词汇检测与分割",
    ],
    metrics="COCO 零样本检测 56.8 AP；指代分割任务大幅领先同期模型",
    whyCite="讲「视觉基础模型统一多任务」时引用；是「检测器 + 基础模型」双组件范式里关键的一环。"),
"2311.17132": dict(
    theme="backbone", venue="CVPR 2024", in_window=False,
    titleZh="TransNeXt：鲁棒的注视点式视觉感知 Transformer",
    coreIdea="提出聚合邻域注意力——在局部窗口内把 query 与其邻近 key/value 一并聚合，用连续位置偏置与可学习半径刻画人类注视点的聚集特性，兼顾线性复杂度与密集目标表现。",
    innovation=[
        "聚合邻域注意力（Aggregated Neighborhood Attention）",
        "连续位置偏置建模跨窗口的相对位置关系",
        "可学习聚合半径，自适应分配注意力范围",
        "分类 / 检测 / 分割三任务通用骨干",
    ],
    metrics="COCO 检测 AP 51.8 量级，同参数量下优于 ConvNeXt 与 Swin",
    whyCite="讨论「注意力骨干 vs 卷积骨干」时的近期代表；也适合作为「换骨干做消融」的实验素材。"),
"2401.10166": dict(
    theme="backbone", venue="NeurIPS 2024 (Spotlight)", in_window=True,
    titleZh="VMamba：视觉状态空间模型",
    coreIdea="把状态空间模型（SSM）引入视觉骨干，用选择性扫描沿四个方向在图像上做线性复杂度建模，以卷积级别的速度获得全局感受野，替代自注意力的平方复杂度。",
    innovation=[
        "视觉 SSM 骨干 + 跨方向扫描的二维状态空间建模",
        "选择性扫描机制，按输入内容自适应决定保留或丢弃信息",
        "与 CNN 同为线性复杂度，可扩展到高分辨率输入",
        "VSSM 系列即插即用，可直接替换 DETR / YOLO 的骨干",
    ],
    metrics="吞吐与卷积相当；检测 / 分割上优于同规模 ViT 与 Swin",
    whyCite="谈小目标、高分辨率任务的骨干选择，或介绍 SSM 视觉化时引用；「视觉 Mamba」这一支的代表作。"),
"2401.17270": dict(
    theme="ovod", venue="CVPR 2024", in_window=True,
    titleZh="YOLO-World：实时开放词汇目标检测",
    coreIdea="在 YOLO 的文本—图像骨干上做重参数化，把离线训练好的文本嵌入「蒸馏」进一个图像嵌入分支，推理时只需文本嵌入 + 图像嵌入即可检测任意文本类别，同时保住 YOLO 的速度。",
    innovation=[
        "文本—图像骨干重参数化：训练用文本分支，推理用图像分支",
        "文本嵌入预训练 + 对比预训练增强文本—图像对齐",
        "以 CLIP 图像嵌入作为「语言引导」，桥接任意文本输入",
        "保持 YOLO 级实时速度，可直接输出开放词汇检测结果",
    ],
    metrics="COCO 约 55 AP 量级；多提示词 mAP 与单提示词接近",
    whyCite="开放词汇与实时之间的折中方案；写「实时开放词汇」或与 Grounding DINO 做速度对比时引用。"),
"2402.13616": dict(
    theme="realtime", venue="ECCV 2024", in_window=True,
    titleZh="YOLOv9：用可编程梯度信息学习你想学的东西",
    coreIdea="发现深层网络中梯度信息在反向传播中会因「深度监督不足」和「梯度融合」而丢失，于是设计可编程梯度信息（PGI）生成器，在骨干与 neck 之间插入辅助分支把梯度信息回传到浅层。",
    innovation=[
        "PGI 可编程梯度信息生成器",
        "骨干加辅助分支 A2 / B2，把输入层梯度信息引回浅层",
        "GELAN 通用高效层聚合 neck，提升特征融合效率",
        "无需大规模数据集预训练即可稳定训练",
    ],
    metrics="COCO AP 47.0 / 47.1（L 级），超过同规模 YOLOv8 且参数更少",
    whyCite="讨论「训练信号与推理不一致」「梯度信息丢失」时引用；是 YOLO 近年最重要的机理型改进。"),
"2405.14458": dict(
    theme="realtime", venue="NeurIPS 2024", in_window=True,
    titleZh="YOLOv10：实时端到端目标检测",
    coreIdea="指出一阶段检测器推理时仍需 NMS，这是训练 / 推理不一致的根源，于是引入一致性双重标签分配——训练时同时跑 1:1（无 NMS）与 1:N（NMS）两条分支，推理时只用 1:1 分支。",
    innovation=[
        "一致性双重标签分配：训练期 1:1 与 1:N 双分支并行监督",
        "推理期只保留 1:1 分支，彻底去掉 NMS",
        "引入面向小目标的全标签分配正则项",
        "无需预训练权重或定制算子，部署成本低",
    ],
    metrics="COCO AP 46.3（L 级）；相对 YOLOv9 速度提升约 1.8×、模型体积降至约 1/2.8",
    whyCite="讨论「NMS-free 的一阶段检测」时引用；与 RT-DETR 的 NMS-free 路线可以直接对照着写。"),
"2408.00714": dict(
    theme="foundation", venue="ICLR 2025", in_window=True,
    titleZh="SAM 2：对图像和视频做万物分割",
    coreIdea="把 SAM 的分割架构扩展到视频——提出流式记忆机制，按帧增量地把上一帧的分割结果编码进记忆库，使模型能在视频上同时处理物体提示与点击提示并保持时序一致。",
    innovation=[
        "流式记忆机制 + 记忆银行 + 记忆注意力",
        "统一图像与视频的提示分割接口",
        "面向提示的时序一致性训练数据生成管线",
        "开放世界的可提示视频对象分割",
    ],
    metrics="视频分割基准上大幅超越此前方法；SA-V 分割表现尤为突出",
    whyCite="讨论「检测 + 分割协同」或「视觉基础模型的时序扩展」时引用；是与检测器天然互补的一环。"),
"2410.13842": dict(
    theme="end2end", venue="ICLR 2025", in_window=True,
    titleZh="D-FINE：把 DETR 的回归任务重新定义为细粒度分布细化",
    coreIdea="认为 L1 回归是 DETR 定位精度的瓶颈，于是把回归从「预测一个坐标」改成「预测一个以真值为中心的离散分布」，再对分布做细化，把定位精度整体抬高一个档次。",
    innovation=[
        "FDR 细粒度分布细化：预测离散分布而非单点坐标",
        "GDR 全局分布细化：借高层特征迭代优化整层分布",
        "分布式回归天然编码了定位不确定性",
        "可直接叠加到 DINO / DEIM 等已有框架上",
    ],
    metrics="COCO ResNet-50 AP 54.3；12 epoch 训练即超越此前最好结果",
    whyCite="讨论「回归形式」「定位精度瓶颈」时引用；与 DEIM 的匹配改进构成两条正交的技术线。"),
"2412.04234": dict(
    theme="end2end", venue="CVPR 2025", in_window=True,
    titleZh="DEIM：用改进的匹配实现快速收敛的 DETR",
    coreIdea="指出密集一对一匹配能提供更丰富的正样本监督，从而在同样的 12 epoch 内比 DINO 收敛得更快；同时用匹配性感知损失抑制低质量匹配对训练的干扰。",
    innovation=[
        "Dense O2O 密集一对一匹配：每个 GT 取 Top-K 个高重叠 Query",
        "匹配性感知损失 MAL：按匹配质量给分类 / 回归损失加权",
        "保持一对一推理特性，不引入额外推理延迟",
        "可直接叠加到 DINO / D-FINE 上形成复合收益",
    ],
    metrics="COCO AP 50.6（ResNet-50，12 epoch），对比 DINO 的 49.0",
    whyCite="讨论「收敛速度」「正样本数量」时引用；是 DINO → DEIM → D-FINE 这条叙事线里的关键一环。"),
"2502.12524": dict(
    theme="realtime", venue="arXiv 2025", in_window=True,
    titleZh="YOLOv12：以注意力为中心的实时目标检测器",
    coreIdea="认为实时检测器过去只卷积不用注意力，是出于「注意力太贵」的误解；于是把注意力高效化（区域注意力 + 块注意力 + FlashAttention），做成以注意力为中心的架构，速度不变而精度上台阶。",
    innovation=[
        "区域注意力 A2：在区域之间共享上下文，注意力只在区域内计算",
        "块注意力 B2：块内高维注意力，块间用卷积承接",
        "轻量二维位置编码 PosE",
        "FlashAttention 降低注意力开销",
    ],
    metrics="COCO AP 40.6（L 级），延迟与 YOLOv10 / v11 同级而精度更高",
    whyCite="讨论「注意力实时化」「卷积与注意力的权衡」时引用；是 YOLO 系列最新的架构方向。"),
"2508.10104": dict(
    theme="foundation", venue="arXiv 2025", in_window=True,
    titleZh="DINOv3：面向工业级视觉任务的第二代自监督基础模型",
    coreIdea="把自监督视觉预训练扩展到超大规模无标签互联网图像与 7B 参数级模型，产出兼具高层语义与稠密空间信息的通用视觉骨干，并用 Gram 锚定与高分辨率适配支撑像素级任务。",
    innovation=[
        "超大规模自监督训练（7B 参数级）与海量无标签数据",
        "Gram 锚定：用自相似矩阵稳定稠密特征",
        "高分辨率适配：高分辨率推理与位置编码插值",
        "冻结骨干即可在检测 / 分割上带来大幅提升",
    ],
    metrics="冻结骨干在 COCO / LVIS 分割检测上显著超过此前自监督模型",
    whyCite="讨论「自监督基础模型的最新进展」或「冻结骨干 vs 全量微调」时引用。"),
}

# ── 2025-10 ~ 2026-10 窗口内新增（从 arXiv 检索得到）──
ANNOT2 = {
"2610.09502": dict(
    theme="realtime", venue="arXiv 2026-10", in_window=True,
    titleZh="RT-DETR-World：把大语言模型的丰富语义迁移到实时开放词汇检测",
    coreIdea="指出紧凑型实时检测器难以吸收丰富的实例语义，于是构建 GroundingCapv2 三级监督（类别名 / 物体描述 / 图像描述），把属性、动作、状态与上下文关系在训练期灌进检测器，推理期仍保持轻量的 query—文本匹配。",
    innovation=[
        "GroundingCapv2 数据集：类别名 / 实例级描述 / 图像级描述三级语义监督",
        "双路描述对齐 DDA：部署一致的 MiniLM 路径与非语言模型路径共同对齐",
        "描述只用于训练期，推理期保持紧凑的 query—文本匹配，不增加推理成本",
    ],
    metrics="在实时开放词汇基准上以紧凑模型取得领先精度（详见原文表格）",
    whyCite="讨论「实时检测器如何吸收 LLM 语义」或「训练期监督注入」时引用；是 2026 年实时开放词汇方向的代表作。"),
"2603.07022": dict(
    theme="end2end", venue="arXiv 2026-03", in_window=True,
    titleZh="OV-DEIM：带网格合成增广的实时 DETR 式开放词汇目标检测",
    coreIdea="现有实时开放词汇检测几乎都建在 YOLO 系模型上，而 DETR 式方案在延迟、轻量化与整体性能上都落后；OV-DEIM 在最新的 DEIMv2 框架上构建端到端 DETR 式开放词汇检测器，并整合视觉语言建模做高效推理。",
    innovation=[
        "基于 DEIMv2 的端到端 DETR 式开放词汇检测器，兼顾延迟与轻量化",
        "查询补充策略：在不牺牲推理速度的前提下提升 Fixed AP",
        "GridSynthetic 网格合成增广：一次前向内组合多个训练样本",
        "用更丰富的共现关系与空间布局缓解噪声定位对分类损失的污染",
    ],
    metrics="实时开放词汇基准上取得领先的整体性能与 Fixed AP（详见原文）",
    whyCite="写「端到端检测器如何做开放词汇」或「增广策略影响分类损失」时引用；是 DEIM 系列的最新延伸。"),
"2609.26092": dict(
    theme="end2end", venue="arXiv 2026-08", in_window=True,
    titleZh="Match One, Learn with Graph：面向目标检测的一对一图查询协作与反向共享",
    coreIdea="指出 O2O 匹配下，一个目标的最佳分类、中心、尺度与重叠证据往往分散在多个 query 上，只有被匹配的「属主」拿到正监督——作者称之为「query 知识碎片化」；BS-O2G 用稀疏的预测感知图组织 query 协作，同时完整保留原 O2O 匹配器、正标签与目标函数。",
    innovation=[
        "提出并命名「query 知识碎片化」问题",
        "O2G 图上校准：在前向传播相对消息，聚合各 query 上的互补证据",
        "Backward Sharing：复用转置且去梯度的邻接矩阵，在持久 query 基向量之间路由梯度",
        "不改动匹配器与推理结构，可即插即用地挂在不同 DETR 上",
    ],
    metrics="在多种 DETR、多种骨干、COCO 与 CrowdHuman 上一致提升，且收敛更快",
    whyCite="讨论「一对一匹配的信息瓶颈」或「正样本监督不足」时引用；是 DEIM 之后查询侧改进的新思路。"),
"2605.10190": dict(
    theme="ovod", venue="arXiv 2026-05", in_window=True,
    titleZh="DetRefiner：基于特征融合 Transformer 的模型无关检测精修",
    coreIdea="开放词汇检测受限于全局与局部上下文线索融合不足，DetRefiner 提出即插即用的精修框架：把基础模型（DINOv3 等）的全局图像特征与 patch 级特征送进轻量 Transformer 编码器，产出一个类别向量与一组 patch 向量，据此推断属性可靠性并重标定基础检测器的置信度。",
    innovation=[
        "全局 / 局部特征融合 Transformer，同时输出类别向量与 patch 向量",
        "属性可靠性推断：据此重标定基础检测器的置信度分数",
        "与基础 OVOD 模型解耦训练——既不需要访问其内部特征，也不需要重训",
        "推理时只消费基础检测器的预测结果，不侵入主干结构",
    ],
    metrics="在 COCO / LVIS / ODinW13 / Pascal VOC 上对多个 OVOD 模型一致提升，新类别最多 +10.1 AP",
    whyCite="写「后处理式精修」「置信度校准」或「检测器 + 基础模型协作」时引用；是 2026 年开放词汇方向易复现的改进。"),
"2610.05191": dict(
    theme="realtime", venue="arXiv 2026-10", in_window=True,
    titleZh="Order Matters：面向 RNN 式目标检测的竞争引导查询排序",
    coreIdea="没有显式去重时，多个 query 仍会对同一目标给出高度相似的假设，导致训练不稳、预测不果断；借鉴 NMS 的顺序性，DETRNN 把无序的 object query 变成「竞争感知的序列」，再用 RNN 沿这个序列循环精修。",
    innovation=[
        "基于置信度与相似度的显式排序，把无序 query 组织成有序序列",
        "RNN 沿排序做竞争感知的循环精修，在 decoder 内部建模 query 间的竞争",
        "抑制冗余预测、稳定优化过程，同时保持与 NMS-free 推理的兼容",
    ],
    metrics="在多个 DETR 系检测器上取得一致提升，且效率基本不变",
    whyCite="讨论「NMS-free 仍会出重复框」或「查询冗余与排序」时引用；把 NMS 的先验巧妙搬进 decoder 内部。"),
"2606.00782": dict(
    theme="ovod", venue="arXiv 2026-05", in_window=True,
    titleZh="FlowOVD：用生成式潜流做零样本开放词汇检测",
    coreIdea="现有开放词汇检测把 decoder query 当成静态的或仅由编码器特征初始化，限制了查询的多样性与灵活性；FlowOVD 改用生成式视角，把 query 生成建模为潜空间中的连续传输过程。",
    innovation=[
        "用 rectified flow 把「文本无关 query」连续地搬运成「文本引导 query」",
        "文本条件的生成式查询生成，取代启发式离散 query 构造",
        "连续潜空间动力学带来更有表达力的语义对齐",
        "无需任何额外训练数据",
    ],
    metrics="COCO 49.5 AP、LVIS 31.5 AP；较 Grounding DINO 分别 +1.2 AP 与 +4.1 AP",
    whyCite="写「生成式 / 扩散式检测」或「query 初始化机制」时引用；与 DiffusionDet 是同一支思路的现代版。"),
"2608.30247": dict(
    theme="ovod", venue="arXiv 2026-08", in_window=True,
    titleZh="OPUS：一个简洁而有效的统一开放词汇检测框架",
    coreIdea="反思统一开放词汇检测是否真的需要繁重的跨模态融合、分阶段训练与迭代式标注管线；结论是——在基础模型更强的今天，靠语义丰富的视觉表示 + 可扩展的接地监督就能把统一 OVD 做得很简单。",
    innovation=[
        "三段式极简架构：语义视觉编码器 + 高效混合编码 + 提示感知解码器",
        "统一支持文本 / 交互视觉 / 通用视觉 / 混合四类提示，且不设提示专用分支",
        "一阶段文本-视觉训练策略 + 实例级对比对齐（ICA）",
        "基于 SAM3 的单遍数据引擎，自动生成异质接地监督",
    ],
    metrics="在 COCO、LVIS-minival、ODinW35 等基准上验证（详见原文）",
    whyCite="讨论「开放词汇检测要不要做得很复杂」时引用；是一篇方法论意义上很有分量的「做减法」论文。"),
"2606.09360": dict(
    theme="ovod", venue="arXiv 2026-06", in_window=True,
    titleZh="ExDet：带跨模态外推与校正的开放域开放词汇检测",
    coreIdea="开放域开放词汇检测（ODOVD）要求同时泛化到新类别与新域，而现有做法把开放词汇检测器与域泛化模块一起从头训练、成本高昂；ExDet 提出轻量的「类别—域协同泛化」框架，即插即用地增强已有检测器。",
    innovation=[
        "TGE 文本引导外推：利用视觉语言模型的 DeltaSpace 性质，从文本推出类别 / 域感知的代理视觉原型",
        "DCR 检测器兼容校正：以免训练、免真实数据的方式学习，把表示校正回检测器友好的源域分布",
        "ExRPN：结合语义相似度与 RPN 置信度重标定候选框分数，提升新类别召回",
    ],
    metrics="在开放域 OVD 基准上同时提升新类别与新域的泛化能力（详见原文）",
    whyCite="写「域泛化 + 开放词汇」或「免训练校正」时引用；是开放域这一子方向的代表工作。"),
"2610.33430": dict(
    theme="end2end", venue="arXiv 2026-10", in_window=True,
    titleZh="Dynamic Query as Budgeting：把小目标检测的动态查询重述为「预算分配」",
    coreIdea="指出 DETR 系小目标检测器的动态查询机制把两件事纠缠在一起——解多少个 query、以及选哪些 query；实验证明动态查询的主要作用是「预算分配」（按目标密度分配解码容量），而非精细的查询选择。",
    innovation=[
        "把动态查询重述为单调且保守的预算分配原则",
        "轻量、非学习的 budgeter：由编码器置信度估计输入相关的 query 预算 K(x)",
        "保留标准 Top-K(x) 查询初始化，不引入额外学习模块或启发式过滤",
        "直接消掉了预算器里的选择误差来源",
    ],
    metrics="800×800 分辨率下 BUTR-L 在 AI-TOD-v2 达 35.7 AP / 47.8 FPS，在 VisDrone 达 29.8 AP / 42.1 FPS（T4）",
    whyCite="讨论「动态查询到底在做什么」或「小目标的 query 预算如何定」时引用；对小目标方向尤其有用。"),
"2610.27479": dict(
    theme="ovod", venue="arXiv 2026-10", in_window=True,
    titleZh="FocusOVD：面向开放词汇小目标检测的几何与上下文特征精修",
    coreIdea="开放词汇检测在小目标上受限于高分辨率细节保留不足、跨层特征聚合无效、区域判别力有限三个问题；FocusOVD 在不改动冻结 VLM 骨干的前提下，用三个互补模块增强小目标表征。",
    innovation=[
        "加权跨尺度特征融合：学习归一化的逐层权重，平衡浅层外观细节与深层语义",
        "残差风车形门控卷积：强化高分辨率特征中的局部几何响应",
        "残差卷积门控线性单元：抑制背景主导的激活，提升 RoI 判别力",
    ],
    metrics="COCO-OVD 上新类别 AP 达 36.3%，超过 CORA、UniDet 等对比方法",
    whyCite="把「开放词汇」与「小目标」两条线接起来时引用；这是目前少见的同时覆盖两者的组合。"),
"2608.28706": dict(
    theme="backbone", venue="arXiv 2026-08", in_window=True,
    titleZh="VGTok：面向高分辨率目标检测的可变粒度 Tokenization",
    coreIdea="ViT 检测器在进入任何学习模块之前就固定了统一的 token 网格，原生分辨率的航拍检测器只能在「解析几像素目标」与「守住算力显存上限」之间二选一；VGTok 是一个免训练 tokenizer，在编码之前按区域从像素出发设定 patch 粒度。",
    innovation=[
        "以多尺度形态学 top-hat 可分性为每个区域打分，按每图像分位数阈值锁定 token 预算",
        "结构张量门控（λ_min）：只在二维目标结构成立处细化，一维杂乱保持粗粒度",
        "产出的 token 集合是图像的严格划分，无重复无遗漏",
        "训练无关，可作为冻结 checkpoint 的即插即用模块",
    ],
    metrics="Co-DETR + EVA-02 ViT-L 在 VisDrone-val 上 40% token 预算即达 44.22 AP，密集设定 48.38 AP（较最强已发表结果 +6.08）；AI-TOD-v2 达 37.27 AP",
    whyCite="讨论「高分辨率 / 密集小目标」与「token 预算」时引用；把「分辨率—算力矛盾」换了个问法，值得借鉴。"),
"2605.03642": dict(
    theme="ovod", venue="arXiv 2026-05", in_window=True,
    titleZh="The Detector Teaches Itself：面向开放词汇检测的轻量自监督适配",
    coreIdea="协作范式中 VLM 是在整图上预训练的，难以捕捉局部目标细节，限制了它在区域级检测中的作用；DAT 用闭集检测器构造「区域感知伪标注」数据集，来自监督地微调 VLM 的视觉骨干。",
    innovation=[
        "区域感知伪标注：新类别区域可能未标注或被误标，但仍参与训练",
        "解耦式微调 + 权重插值：增强局部对齐的同时保留全局语义",
        "即插即用、零推理开销，微调参数不到 0.8M",
    ],
    metrics="在 COCO 与 LVIS 上稳定提升协作式开放词汇检测效果",
    whyCite="讨论「VLM 特征不适合区域级任务」或「检测器与 VLM 互相教学」时引用；思路轻巧，适合做课程里的复现实验。"),
}
ANNOT.update(ANNOT2)

THEME_ZH = {
    "end2end": "端到端 DETR 系",
    "realtime": "实时检测",
    "ovod": "开放词汇检测",
    "foundation": "视觉基础模型",
    "backbone": "骨干网络",
}

papers = []
for pid, ann in ANNOT.items():
    m = meta_by_id.get(pid)
    if not m:
        print("!! missing meta for", pid)
        continue
    papers.append({
        "id": pid,
        "arxivUrl": "https://arxiv.org/abs/" + pid,
        "title": m["title"],
        "titleZh": ann["titleZh"],
        "published": m["published"],
        "updated": m["updated"],
        "authors": m["authors"],
        "venue": ann["venue"],
        "abstract": m["abstract"],
        "tags": m.get("cats", []),
        "theme": ann["theme"],
        "themeZh": THEME_ZH[ann["theme"]],
        "inWindow": ann["in_window"],
        "coreIdea": ann["coreIdea"],
        "innovation": ann["innovation"],
        "metrics": ann["metrics"],
        "whyCite": ann["whyCite"],
    })

papers.sort(key=lambda p: (p["theme"], p["published"]))

with io.open(os.path.join(DATA, "object-detection-papers.json"), "w", encoding="utf-8") as f:
    f.write(json.dumps(papers, ensure_ascii=False, indent=2))

from collections import Counter
c = Counter(p["theme"] for p in papers)
print("共 %d 篇" % len(papers))
print("主题分布:", dict(c))
print("窗口内(2023-10 起):", sum(1 for p in papers if p["inWindow"]))
