# SKC5053 深度学习专业课 · 教学资源下载

> **课程**：深度学习 · 从原理到工业级实战（9 章 + 7 大实验 · 54 学时）
> **版本**：v3.1.4（2026-09-19）
> **许可**：教学使用 · 可商用 · 需保留原作者署名

---

## 📚 核心资源

### 🎓 教学课件

| 资源 | 链接 | 大小 | 说明 |
|------|------|------|------|
| **完整课件 PPT**（18 页）| [SKC5053_教学课件_小陶老师.pptx](../SKC5053_教学课件_小陶老师.pptx) | 62KB | 紫色 AI 科技风 · 9 章节 · 实验分布 |
| **章节导图**（9 张 PNG）| 见 GitHub `assets/images/dl-course/` | - | 每章思维导图 |

### 💻 实验代码（7 大实验）

| 实验 | 难度 | 时长 | 技术栈 |
|------|------|------|--------|
| L1 PyTorch 张量与自动微分 | ⭐ | 2 学时 | PyTorch + CUDA |
| L2 MLP 手写数字识别 | ⭐ | 2 学时 | MNIST + 反向传播 |
| L3 CNN 图像分类 | ⭐⭐ | 4 学时 | ResNet + CIFAR-10 |
| L4 YOLOv8 + U-Net 检测 | ⭐⭐⭐ | 4 学时 | Ultralytics + 自采数据集 |
| L5 LSTM 情感分析 | ⭐⭐ | 4 学时 | IMDB + Padding |
| L6 BERT 微调 | ⭐⭐⭐ | 6 学时 | HuggingFace + 注意力 |
| L7 DCGAN + 迁移学习 | ⭐⭐⭐⭐ | 12 学时 | GAN + 对抗训练 |

> **代码地址**：https://github.com/Taoj2025/SKC5053-experiments （示例代码）

### 📖 推荐阅读（核心论文）

#### CNN 经典
- **ResNet** · He et al. 2016 · [arxiv:1512.03385](https://arxiv.org/abs/1512.03385)
- **VGG** · Simonyan & Zisserman 2014 · [arxiv:1409.1556](https://arxiv.org/abs/1409.1556)
- **AlexNet** · Krizhevsky et al. 2012 · [NeurIPS](https://papers.nips.cc/paper_files/paper/2012/hash/c399862d3b9d6b76c8436e924a68c45b-Abstract.html)

#### 大模型时代
- **Attention Is All You Need** · Vaswani et al. 2017 · [arxiv:1706.03762](https://arxiv.org/abs/1706.03762)
- **BERT** · Devlin et al. 2018 · [arxiv:1810.04805](https://arxiv.org/abs/1810.04805)
- **GPT-3** · Brown et al. 2020 · [arxiv:2005.14165](https://arxiv.org/abs/2005.14165)

#### 生成模型
- **GAN** · Goodfellow et al. 2014 · [NeurIPS](https://papers.nips.cc/paper_files/paper/2014/hash/5ca3e9b1f4c241bd1c4c2c9c3e3a8f7e-Abstract.html)
- **Stable Diffusion** · Rombach et al. 2022 · [arxiv:2112.10752](https://arxiv.org/abs/2112.10752)

### 🛠️ 工具栈

```yaml
# 云端环境
hardware: NVIDIA A10 24GB（云端 Ubuntu）
OS: Ubuntu 20.04 LTS

# 软件栈
python: 3.10
pytorch: 2.6.1
cuda: 12.4
jupyter: 最新版
experiment_tracking: Weights & Biases
```

### 📊 数据集

| 数据集 | 来源 | 规模 | 用途 |
|-------|------|------|------|
| MNIST | torchvision | 7 万张 | L2 MLP 手写数字 |
| CIFAR-10 | torchvision | 6 万张 | L3 CNN 图像分类 |
| 自采葡萄叶片 | 自采 | 1 万张 | L4 YOLOv8 检测 |
| IMDB | HuggingFace | 5 万条 | L5 LSTM + L6 BERT |

---

## 🎯 4 大实战项目（毕设级）

### 项目 1：医疗影像 · 肺部 X 光诊断
- **技术**：ResNet 微调
- **指标**：92.3% 准确率
- **商业价值**：AI 辅助放射科医生
- **代码**：见 SKC5053-experiments 项目

### 项目 2：自动驾驶 · 葡萄病虫害检测
- **技术**：YOLOv8n
- **指标**：mAP@0.5 76.5%
- **商业价值**：智慧农业 + 边缘部署
- **部署**：RTX 4090 + 树莓派

### 项目 3：电商客服 · IMDB 情感分析
- **技术**：BERT 微调
- **指标**：92.7% 准确率
- **商业价值**：智能客服 + 多任务

### 项目 4（毕设推荐）：AIGC · DCGAN 图像生成
- **技术**：DCGAN + 迁移学习
- **指标**：FID 分数 + 论文级
- **商业价值**：内容生成 SaaS

---

## 📝 评分标准

| 维度 | 占比 | 评分 |
|------|------|------|
| 数据加载 | 10% | R1-R2 |
| 模型搭建 | 15% | R3 |
| 训练调参 | 20% | R4-R5 |
| 评估分析 | 15% | R6 |
| 文档报告 | 15% | R7-R8 |
| 创新扩展 | 15% | R9 |
| 协作反思 | 10% | R10 |

## 🎓 课程对标

| 国际课程 | 我们的差异化 |
|---------|------------|
| Coursera Deep Learning（吴恩达）| 加上国产工业级实战案例 |
| fast.ai Practical DL | 加上云端 A10 GPU 实验 |
| CS231n（李飞飞）| 加上 BERT/GPT/扩散模型前沿 |

## 📧 教学支持

- **答疑群**：每周三/日晚 20:00-21:00
- **GitHub Issues**：https://github.com/Taoj2025/SKC5053-experiments/issues
- **邮件**：见 GitHub 个人主页

---

*资源版本 v3.1.4 · 教学使用 · 可商用 · 需保留原作者署名*
*生成工具：小Q AI 协作整理 · 适配 SKC5053 课程大纲*