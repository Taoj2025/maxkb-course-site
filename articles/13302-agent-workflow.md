---
id: 13302
title: "Agent 工作流设计实战案例"
date: 2026-07-24
tags: ["Agent"]
summary: "单 Agent / 多 Agent / 工具调用 / 任务分解 4 大模式 + 完整代码"
---

# 🤖 Agent 工作流设计实战案例

## 模式 1：单 Agent（基础）

适合简单问答场景，1 个 Agent 处理 1 个任务。

```
用户提问 → Agent 思考 → 调用 LLM → 返回答案
```

## 模式 2：多 Agent 协同（进阶）

适合复杂任务，多个 Agent 分工协作。

```
用户提问 → 调度 Agent → 
  ├→ 检索 Agent（查知识库）
  ├→ 推理 Agent（数学计算）
  └→ 生成 Agent（写文案）
→ 综合答案
```

## 模式 3：工具调用（Tools）

Agent 可调用外部工具：搜索、计算、API 等。

## 模式 4：任务分解（Planning）

Agent 把复杂任务拆解为子任务，逐步执行。

```
用户：「规划 3 天广州旅游」
Agent 拆解：
  Day 1: 陈家祠 → 沙面岛 → 上下九
  Day 2: 白云山 → 北京路
  Day 3: 长隆野生动物世界
→ 输出详细行程
```

## 📦 完整代码示例（Python SDK）

```python
from maxkb.agent import Agent, Tool

# 定义工具
weather_tool = Tool(
    name="get_weather",
    description="查询城市天气",
    params={"city": "string"}
)

# 创建 Agent
agent = Agent(
    name="trip_planner",
    llm="gpt-4",
    tools=[weather_tool],
    system_prompt="你是专业的旅游规划师"
)

# 执行
result = agent.run("帮我规划 3 天广州旅游")
print(result)
```

## 🎯 工作流设计原则

- **单一职责**：每个 Agent 只做一件事
- **明确输入输出**：每个节点都有清晰 contract
- **错误处理**：每个步骤都要 try/except
- **可观测性**：每个 Agent 都有日志和监控

👉 [获取完整工作流设计手册](https://taoj2025.github.io/maxkb-course-site/)
