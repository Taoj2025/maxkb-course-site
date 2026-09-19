/**
 * GET /api/dl-course
 *
 * 返回 SKC5053 深度学习课程完整数据：
 * - 9 章课程
 * - 7 大实验
 * - 3 集抖音短视频链接
 * - 18 页 PPT 链接
 *
 * 部署位置：Vercel Serverless Function
 * 数据源：硬编码（教学场景 · 静态数据）
 * 
 * 安全设计：
 * - 无敏感数据泄露
 * - 仅公开教学信息（不暴露 JWT / 数据库凭证）
 * - CORS 允许 taoj2025.github.io 同源 + taotaoedu.ltd 自定义域名
 */

// 课程数据
const COURSE_DATA = {
    meta: {
        courseCode: 'SKC5053',
        courseName: '深度学习专业课',
        instructor: '小陶老师',
        institution: '本校',
        college: '人工智能学院',
        credits: 3,
        hours: 54,
        theoryHours: 18,
        experimentHours: 36,
        semester: '2026-2027-1',
        objectGrade: '23本数据科学与大数据技术[1-2] 大三选修',
        assessmentMethod: '考查',
        classroom: '单双周 8/10 课时',
    },
    chapters: [
        {
            id: 1,
            num: '第 1 章',
            title: 'AI 概述与数学基础',
            hours: 2,
            type: 'theory',
            keyConcepts: ['AI 发展史 4 大浪潮', '线性代数', '微积分', '概率统计'],
            coreMath: ['矩阵运算', '梯度下降', '链式法则'],
            recommendedMaterials: ['吴恩达 Machine Learning 课程', '周志华《机器学习》'],
        },
        {
            id: 2,
            num: '第 2 章',
            title: '全连接神经网络（MLP）',
            hours: 2,
            type: 'theory',
            keyConcepts: ['感知机', '反向传播', '激活函数', '优化器'],
            coreMath: ['梯度下降', '链式法则', 'SGD / Adam'],
            recommendedMaterials: ['PyTorch 官方教程', 'Deep Learning Book'],
        },
        {
            id: 3,
            num: '第 3 章',
            title: 'CNN 卷积神经网络',
            hours: 3,
            type: 'core',
            keyConcepts: ['卷积层', '池化层', 'LeNet', 'AlexNet', 'VGG'],
            coreMath: ['卷积运算', '感受野', '参数共享'],
            recommendedMaterials: ['CS231n 卷积神经网络', 'ResNet 论文'],
        },
        {
            id: 4,
            num: '第 4 章',
            title: 'ResNet 与现代 CNN',
            hours: 3,
            type: 'key',
            keyConcepts: ['残差连接', '深度网络训练', 'ResNet-18/50/101', 'BatchNorm'],
            coreMath: ['恒等映射', '反向传播梯度流'],
            recommendedMaterials: ['He et al. 2016 ResNet 论文', 'EfficientNet 论文'],
        },
        {
            id: 5,
            num: '第 5 章',
            title: 'RNN / LSTM 时序建模',
            hours: 3,
            type: 'theory',
            keyConcepts: ['循环神经网络', 'LSTM 门控', 'GRU', '序列数据处理'],
            coreMath: ['时序反向传播（BPTT）', '梯度消失/爆炸'],
            recommendedMaterials: ['Hochreiter 1997 LSTM 论文', 'Understanding LSTM Networks'],
        },
        {
            id: 6,
            num: '第 6 章',
            title: 'Transformer 注意力机制',
            hours: 3,
            type: 'core',
            keyConcepts: ['Self-Attention', 'Multi-Head', 'Positional Encoding', 'Layer Norm'],
            coreMath: ['QKV 矩阵运算', '缩放点积注意力'],
            recommendedMaterials: ['Vaswani 2017 Attention Is All You Need', 'The Illustrated Transformer'],
        },
        {
            id: 7,
            num: '第 7 章',
            title: 'BERT / GPT 预训练大模型',
            hours: 3,
            type: 'frontier',
            keyConcepts: ['BERT 双向注意力', 'GPT 自回归', '微调 (Fine-tuning)', '下游任务'],
            coreMath: ['掩码语言模型 (MLM)', '下一句预测 (NSP)'],
            recommendedMaterials: ['Devlin 2018 BERT 论文', 'Brown 2020 GPT-3 论文'],
        },
        {
            id: 8,
            num: '第 8 章',
            title: '生成模型（GAN / VAE / 扩散）',
            hours: 3,
            type: 'frontier',
            keyConcepts: ['DCGAN', 'Stable Diffusion', 'Latent Diffusion', '图像生成'],
            coreMath: ['对抗训练', 'KL 散度', 'Score Matching'],
            recommendedMaterials: ['Goodfellow 2014 GAN 论文', 'Rombach 2022 Stable Diffusion'],
        },
        {
            id: 9,
            num: '第 9 章',
            title: '迁移学习与工程化部署',
            hours: 2,
            type: 'practice',
            keyConcepts: ['预训练 + 微调', '边缘部署（Jetson / 树莓派）', 'ONNX', 'TensorRT'],
            coreMath: ['模型蒸馏', '量化（INT8 / FP16）'],
            recommendedMaterials: ['PyTorch 部署教程', 'NVIDIA TensorRT 文档'],
        },
    ],
    experiments: [
        {
            id: 1,
            name: 'PyTorch 张量与自动微分',
            hours: 2,
            tier: 'verified',
            difficulty: '⭐',
            gpu: 'A10 24GB',
            hardPoints: ['理解 autograd 计算图', 'GPU 内存管理'],
            outputMetric: 'GPU 加速比 ≥ 50x',
        },
        {
            id: 2,
            name: 'MLP 手写数字识别',
            hours: 2,
            tier: 'verified',
            difficulty: '⭐',
            gpu: 'A10 24GB',
            hardPoints: ['手写反向传播（不调包）', '激活函数选择'],
            outputMetric: 'MNIST 准确率 ≥ 97%',
        },
        {
            id: 3,
            name: 'CNN 图像分类',
            hours: 4,
            tier: 'comprehensive',
            difficulty: '⭐⭐',
            gpu: 'A10 24GB',
            hardPoints: ['ResNet 残差连接设计', '训练稳定性'],
            outputMetric: 'CIFAR-10 准确率 ≥ 93%',
        },
        {
            id: 4,
            name: 'YOLOv8 + U-Net 工业级检测',
            hours: 4,
            tier: 'comprehensive',
            difficulty: '⭐⭐⭐',
            gpu: 'A10 24GB',
            hardPoints: ['工业级 mAP 调参', '数据不平衡处理'],
            outputMetric: 'mAP@0.5 ≥ 76%',
        },
        {
            id: 5,
            name: 'LSTM 情感分析',
            hours: 4,
            tier: 'comprehensive',
            difficulty: '⭐⭐',
            gpu: 'A10 24GB',
            hardPoints: ['padding / mask / tokenize 三大坑'],
            outputMetric: 'IMDB 准确率 ≥ 89%',
        },
        {
            id: 6,
            name: 'BERT 微调',
            hours: 6,
            tier: 'design',
            difficulty: '⭐⭐⭐',
            gpu: 'A10 24GB',
            hardPoints: ['理解注意力机制', '1.1 亿参数微调'],
            outputMetric: 'IMDB 准确率 ≥ 92%',
        },
        {
            id: 7,
            name: 'DCGAN + 迁移学习（毕设）',
            hours: 12,
            tier: 'design',
            difficulty: '⭐⭐⭐⭐',
            gpu: 'A10 24GB',
            hardPoints: ['对抗训练稳定性', '研究级挑战'],
            outputMetric: 'FID 分数 + 论文级产出',
        },
    ],
    projects: [
        {
            id: 1,
            name: '医疗影像 · 肺部 X 光诊断',
            tech: 'ResNet',
            metric: '92.3% 准确率',
            businessValue: 'AI 辅助放射科医生',
        },
        {
            id: 2,
            name: '自动驾驶 · 葡萄病虫害检测',
            tech: 'YOLOv8n',
            metric: 'mAP 76.5%',
            businessValue: '智慧农业 + 边缘部署',
        },
        {
            id: 3,
            name: '电商客服 · IMDB 情感分析',
            tech: 'BERT 微调',
            metric: '92.7% 准确率',
            businessValue: '智能客服 + 多任务',
        },
    ],
    videos: [
        {
            ep: 'EP1',
            title: '选课前必看：SKC5053 到底有多硬核',
            duration: 52.4,
            url: 'https://taotaoedu.ltd/downloads/SKC5053_EP1_60s.mp4',
        },
        {
            ep: 'EP2',
            title: '7 大实验，一张图看懂难度',
            duration: 55.8,
            url: 'https://taotaoedu.ltd/downloads/SKC5053_EP2_60s.mp4',
        },
        {
            ep: 'EP3',
            title: '3 节课搞定 3 个工业项目',
            duration: 60.5,
            url: 'https://taotaoedu.ltd/downloads/SKC5053_EP3_60s.mp4',
        },
    ],
    ppt: {
        title: 'SKC5053 教学课件',
        pages: 18,
        style: '紫色 AI 科技风',
        size: '62KB',
        downloadUrl: 'https://taotaoedu.ltd/downloads/SKC5053_教学课件.pptx',
    },
    tools: {
        hardware: '云端 Ubuntu + A10 GPU 24GB',
        software: ['PyTorch 2.6.1', 'CUDA 12.4', 'Python 3.10', 'Jupyter Notebook'],
        experimentalTracking: 'Weights & Biases',
    },
    grading: {
        method: 'R1-R10 记录点评分制',
        reportFormat: 'md 格式实验报告',
        selfCheck: '[PASS] 阻断式自检',
    },
};

// Serverless Function
module.exports = async (req, res) => {
    // CORS 配置
    res.setHeader('Access-Control-Allow-Origin', 'https://taoj2025.github.io');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    res.setHeader('Cache-Control', 'public, max-age=3600'); // 缓存 1 小时

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    return res.status(200).json(COURSE_DATA);
};