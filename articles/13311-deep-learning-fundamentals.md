---
id: 13311
title: "深度学习与 LLM 原理：从神经网络到 Agent 调用（6 节系统讲解）"
slug: "deep-learning-fundamentals"
date: "2026-09-12"
category: "课程资料"
author: "小陶老师"
tags: ["深度学习", "Transformer", "LoRA", "Agent", "原理"]
summary: "MaxKB 学员补原理层的必修课。6 节系统讲解神经网络、Transformer、预训练演进、微调与 LoRA、推理优化、Agent 调用。"
---

# 深度学习与 LLM 原理：从神经网络到 Agent 调用

## 1. 引言：为什么 MaxKB 学员要补原理层

MaxKB 是一层"封装层"，把模型加载、RAG 召回、Agent 编排、工具调用都封装成了可视化节点。对学员来说，这层封装极大降低了搭建门槛：拖拽节点就能拼出一个会查知识库、会调 API 的智能体。但封装也会"屏蔽信号"——当输出截断、工具返回乱码、微调后效果没有提升、显存爆掉时，如果不理解底层原理，你只能"猜"出问题在哪一层。本文用 6 节系统补齐从神经网络到 Agent 调用的关键原理，让你在 MaxKB 排错时能定位到具体模块、在做自定义微调时知道 LoRA / QLoRA 在改哪些权重、在部署时懂得 KV-cache 与 vLLM 的关系。

## 2. 神经网络基础（1h）

**感知机的局限**：单层感知机（线性 + 阶跃激活）只能拟合线性可分函数，连经典的 XOR 都分不开。XOR 是线性不可分的——两条直线无论如何画，都没法把 (0,0)/(1,1) 与 (0,1)/(1,0) 分开。解决办法是引入隐藏层与非线性激活，这就是 MLP（多层感知机）。

**MLP 与激活函数**：现代 MLP 通常由 `Linear → ReLU → Linear → ReLU → Linear` 这样的结构堆叠。ReLU 计算简单、梯度不饱和，是隐藏层的默认选择；输出层根据任务选 `Softmax`（多分类）或 `Sigmoid`（二分类）。`Tanh` 在 RNN 时代常用，在 Transformer 中已被 GeLU 取代。

**反向传播直觉**：反向传播就是链式法则的工程实现。前向传播保存每一步的中间结果，反向时从损失出发逐层求 `∂L/∂W`，配合自动求导（PyTorch 的 autograd）几乎不用手写梯度。直觉上，反向传播把"误差"沿着网络从输出端往输入端"倒流"，每一层根据流入的梯度更新自己的权重。

**优化器选择（SGD vs Adam）**：SGD（随机梯度下降）只用一个学习率，对所有参数一视同仁，更新方向易受噪声影响但泛化能力好；Adam 在 SGD 基础上加了一阶矩（均值）和二阶矩（方差）估计，对每个参数自适应学习率。实践默认选 AdamW（Adam 的解耦权重衰减版），训练 LLM 几乎都是它。

```python
# PyTorch MLP 示例：MNIST 分类器
import torch
import torch.nn as nn
import torch.nn.functional as F

class MLP(nn.Module):
    def __init__(self, in_dim=784, hidden=256, out_dim=10):
        super().__init__()
        self.fc1 = nn.Linear(in_dim, hidden)
        self.fc2 = nn.Linear(hidden, hidden)
        self.fc3 = nn.Linear(hidden, out_dim)
        self.dropout = nn.Dropout(0.2)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        return self.fc3(x)            # logits，交给 CrossEntropyLoss

model = MLP()
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
criterion = nn.CrossEntropyLoss()

# 一个最小训练 step
x = torch.randn(32, 784)
y = torch.randint(0, 10, (32,))
logits = model(x)
loss = criterion(logits, y)
loss.backward()        # 反向传播
optimizer.step()       # AdamW 更新参数
optimizer.zero_grad()  # 清空梯度
print(f"loss = {loss.item():.4f}")
```

## 3. Transformer 架构（1.5h）

**为什么替代 RNN**：RNN 串行计算，无法并行、长期依赖靠梯度艰难传递；Transformer 用 self-attention 让任意两个位置直接相连，单步计算就覆盖全部上下文，GPU 并行友好，序列再长也是 O(1) 跳数。

**Self-attention 公式**：

$$
\text{Attention}(Q, K, V) = \text{softmax}\!\left(\frac{QK^\top}{\sqrt{d_k}}\right)V
$$

其中 Q、K、V 由输入向量分别乘三个可学习的投影矩阵得到。`√d_k` 缩放是为了让 softmax 输入不进入饱和区，避免梯度消失。

**Multi-Head 与位置编码**：把 d 维拆成 h 个头（每个头 d/h 维），各自做 attention 再拼接，可以让模型在不同子空间学到不同关系。Self-attention 本身是置换等变的——打乱 token 顺序输出不变，因此必须加位置编码。Sinusoidal 是经典位置编码；RoPE（Rotary Position Embedding）和 ALiBi 是 LLaMA / Mistral 系列的主力。

**Encoder-Decoder**：原始 Transformer（Vaswani et al., 2017）含 Encoder 和 Decoder，Encoder 做双向 attention 用于理解，Decoder 用 masked self-attention 做单向生成。BERT 只用 Encoder，GPT 只用 Decoder，现代 LLM 几乎都是 Decoder-only。

```python
# 手写 single-head attention（PyTorch）
import torch
import torch.nn.functional as F

def single_head_attention(Q, K, V, mask=None):
    d_k = Q.size(-1)
    scores = torch.matmul(Q, K.transpose(-2, -1)) / (d_k ** 0.5)
    if mask is not None:
        scores = scores.masked_fill(mask == 0, float('-inf'))
    attn = F.softmax(scores, dim=-1)
    return torch.matmul(attn, V), attn

batch, seq, d = 2, 5, 8
Q = torch.randn(batch, seq, d)
K = torch.randn(batch, seq, d)
V = torch.randn(batch, seq, d)
out, weights = single_head_attention(Q, K, V)
print("output:", out.shape)        # torch.Size([2, 5, 8])
print("attn weights:", weights.shape)  # torch.Size([2, 5, 5])
```

## 4. 预训练语言模型演进（1h）

**MLM vs CLM**：BERT 用 MLM（Masked Language Modeling）——遮住 15% token 让模型双向预测；GPT 用 CLM（Causal Language Modeling）——从左到右预测下一个 token。MLM 利于理解类任务，CLM 天然适合生成类任务。

**BERT vs GPT vs LLaMA**：BERT 是 Encoder-only、双向、参数量小（Base 110M / Large 340M）；GPT 系列是 Decoder-only、自回归，从 GPT-1 (117M) 一路走到 GPT-3 (175B) 展示了 in-context learning；LLaMA 系列延续 Decoder-only，但用 RoPE、SwiGLU、Grouped-Query Attention 等改进，把"开源可商用 + 强基座"推到主流。

**Decoder-only 主流原因**：一是工程上推理路径清晰（一条自回归链路就能生成）；二是 Scaling Laws 实验显示 CLM 的"下一个 token"损失与下游能力高度相关；三是涌现能力（in-context learning、chain-of-thought）几乎都先在 Decoder-only 大模型上观察到。

**Scaling Laws 简述**：Kaplan 等人（2020）和 Chinchilla（Hoffmann 等，2022）指出，模型损失随参数量、数据量、算力呈幂律下降；Chinchilla 还给出算力最优配比——模型参数量与训练 token 数大致 1:20。在 7B–70B 区间，选择训练 token 数与参数量相当的量级，能在固定算力下取得最佳损失。

```python
# transformers AutoModel：从 HuggingFace Hub 加载任意模型
from transformers import AutoModel, AutoTokenizer

model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

inputs = tokenizer("Hello deep learning", return_tensors="pt")
outputs = model(**inputs)

# outputs.last_hidden_state: [batch, seq_len, hidden_size]
print("last_hidden_state:", outputs.last_hidden_state.shape)
```

## 5. 微调与 LoRA（1.5h）

**全参微调成本**：对一个 7B 模型，全参微调需要保存 optimizer state（Adam 至少 2 倍参数量的动量 + 方差）、梯度、前向激活，显存峰值通常是模型本身的 4–6 倍。一张 24GB 的 4090 跑不动 7B 全参微调。

**LoRA 低秩分解**：LoRA（Hu et al., 2021）冻结原权重 W ∈ ℝ^(d×k)，在旁边并联两个低秩矩阵 A ∈ ℝ^(d×r)、B ∈ ℝ^(r×k)，其中 r ≪ min(d,k)（典型 r=8 或 16）。前向变为 `Wx + BAx`，训练时只更新 A、B。原理上，预训练模型的权重更新矩阵秩很低，所以低秩近似足够。

**QLoRA 4-bit 量化**：QLoRA（Dettmers et al., 2023）把冻结的 W 用 NF4 4-bit 量化存储，再叠 LoRA 适配器。反量化在算子层即时发生，显存占用大幅下降。一张 24GB 显卡即可微调 7B–13B 模型。

**peft 库用法**：`peft.LoraConfig` 配置 rank、alpha、target_modules（注意力投影矩阵名），`get_peft_model` 包装后 `model.print_trainable_parameters()` 可看到可训练参数量从 7B 降到几百万级别。

```python
# LoRA 微调 GPT-2（peft + transformers）
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained("gpt2")

lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["c_attn"],   # GPT-2 的 Q/K/V 合并投影
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# trainable params: ~150K || all params: ~124M || trainable%: 0.12
```

## 6. 推理优化（1h）

**KV-cache**：自回归生成时，每生成一个新 token 都要对所有历史 token 重新算 K、V，严重浪费。KV-cache 把每一步的 K、V 缓存下来，下一步只需算新 token 的 K、V 并拼接，大幅降低 FLOPs 和显存带宽占用，是 vLLM / TGI 等推理引擎的基础。

**量化（INT8/INT4）**：把权重从 FP16 量化到 INT8 或 INT4，能把模型体积和显存占用砍掉一半甚至四分之三。常见方案有 GPTQ（按层量化）、AWQ（激活感知权重量化）、bitsandbytes（推理时动态反量化）。代价是少量精度损失，实际部署中 4-bit 量化 + QLoRA 微调常常已足够。

**vLLM 连续批处理**：传统静态批处理要等整批请求都生成完才能换下一批；vLLM 用 PagedAttention 把 KV-cache 分页管理，实现了"连续批处理"——一个请求生成完可以立刻让位给新请求，GPU 几乎不空转。吞吐量通常比 HuggingFace `generate()` 高 10–20 倍。

```python
# vLLM 部署示例
from vllm import LLM, SamplingParams

llm = LLM(model="facebook/opt-125m")          # 启动推理引擎
sampling_params = SamplingParams(
    temperature=0.8, top_p=0.95, max_tokens=100
)

prompts = ["Deep learning is", "Transformers use"]
outputs = llm.generate(prompts, sampling_params)

for out in outputs:
    print(out.prompt, "->", out.outputs[0].text)
```

## 7. Agent 与工具调用（1h）

**ReAct loop**：ReAct（Yao et al., 2022）把推理（Reasoning）和行动（Acting）交替进行：模型先"思考"下一步要做什么，再调用工具，再观察返回结果继续思考。`Thought → Action → Observation → Thought …` 的循环让 LLM 拥有可调试、可干预的决策链。

**Function Calling**：OpenAI 2023 年发布的 function calling 让 LLM 直接输出结构化的 JSON 参数，开发者把 JSON 解析后去执行真实函数并把结果回填。这把"工具调用"从 prompt 拼接升级到了协议层。

**MCP 协议**：Model Context Protocol（Anthropic 2024 年开源）把"工具描述 + 调用 + 返回"标准化为 JSON-RPC，工具像 USB 设备一样即插即用。MaxKB 的 MCP 节点就是这条思路的工程实现。

**LangChain 用法**：`create_tool_calling_agent` 配合 `@tool` 装饰器定义的工具函数，再交给 `AgentExecutor` 调度，可以快速搭出能调用外部 API 的智能体。

```python
# LangChain create_tool_calling_agent 示例
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

@tool
def get_word_length(word: str) -> int:
    """Return the length of a word."""
    return len(word)

llm = ChatOpenAI(model="gpt-4o-mini")
tools = [get_word_length]
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
print(executor.invoke({"input": "How many letters in the word 'hello'?"}))
```

## 8. 推荐学习路径

建议三阶段推进。第一阶段看 Andrej Karpathy 的"Neural Networks: Zero to Hero"系列 YouTube 视频，从零手写反向传播、GPT，建立直觉。第二阶段跟 HuggingFace 官方课程（NLP Course / Agents Course），熟悉 transformers、peft、trl、vLLM 的标准用法，能跑通微调 + 部署流水线。第三阶段回到论文原文——Attention is All You Need、GPT-3、LoRA、QLoRA、Chinchilla、ReAct，每一篇先看摘要+引言+图表，再选择性精读方法章节。配合本文的 6 节代码逐节复现，能在 4–6 周内把原理层补齐。

## 9. 参考资料

1. Vaswani et al. *Attention Is All You Need.* https://arxiv.org/abs/1706.03762
2. Devlin et al. *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding.* https://arxiv.org/abs/1810.04805
3. Brown et al. *Language Models are Few-Shot Learners.* https://arxiv.org/abs/2005.14165
4. Touvron et al. *LLaMA: Open and Efficient Foundation Language Models.* https://arxiv.org/abs/2302.13971
5. Kaplan et al. *Scaling Laws for Neural Language Models.* https://arxiv.org/abs/2001.08361
6. Hoffmann et al. *Training Compute-Optimal Large Language Models (Chinchilla).* https://arxiv.org/abs/2203.15556
7. Hu et al. *LoRA: Low-Rank Adaptation of Large Language Models.* https://arxiv.org/abs/2106.09685
8. Dettmers et al. *QLoRA: Efficient Finetuning of Quantized LLMs.* https://arxiv.org/abs/2305.14314
9. Yao et al. *ReAct: Synergizing Reasoning and Acting in Language Models.* https://arxiv.org/abs/2210.03629
10. OpenAI. *Function Calling and Other API Updates.* https://openai.com/index/function-calling-and-other-api-updates/
11. Anthropic. *Model Context Protocol Specification.* https://modelcontextprotocol.io/introduction
12. HuggingFace Transformers Documentation. https://huggingface.co/docs/transformers/index
13. HuggingFace PEFT Documentation. https://huggingface.co/docs/peft/index
14. PyTorch Documentation. https://pytorch.org/docs/stable/index.html
15. vLLM Documentation. https://docs.vllm.ai/en/latest/
16. LangChain Documentation. https://python.langchain.com/docs/introduction/
17. Karpathy. *Neural Networks: Zero to Hero.* https://github.com/karpathy/nn-zero-to-hero