---
id: 13307
title: "MCP 协议在前端的落地：让 AI Agent 安全调用你的 API"
date: "2026-07-27"
tags: ["FDE前沿", "MCP", "AI Agent"]
summary: "Model Context Protocol 入门到实战 · 5 分钟给前端项目接入 MCP Server · 真实可运行代码"
category: "最新动态"
color: "purple"
source: "Anthropic 官方文档 + 社区实践"
---

# 🔌 MCP 协议在前端的落地：让 AI Agent 安全调用你的 API

> **采集时间**：2026-07-27 08:00 · **数据源**：Anthropic 官方文档 + 社区实践
> **作者**：小 Q 为小陶老师整理

## 🤔 MCP 是什么？

**MCP（Model Context Protocol）** 是 Anthropic 在 2024 年底开源的 **AI Agent 与工具/数据源通信的标准协议**。截至 2026-07，已有：

- **5000+** 官方/社区 MCP Server
- **30+** 大型软件官方支持（JetBrains、Replit、Sourcegraph 等）
- **3 大浏览器厂商**已宣布支持 MCP

## 🎯 为什么 FDE 必须懂 MCP？

| 场景 | 传统做法 | MCP 做法 |
|---|---|---|
| 让 AI 读取 GitHub Issues | 自己写 Function Calling | 直接用官方 MCP Server |
| 让 AI 操作 Figma | 写 Figma API 适配层 | 用 Figma 官方 MCP |
| 让 AI 写 SQL | 拼 prompt + 解析结果 | 用 DB MCP Server 直连 |

**结论**：未来 1 年，**所有 SaaS 产品都会提供 MCP Server**，不会做的团队会被淘汰。

## 🛠️ 5 分钟给前端项目接 MCP

### Step 1：安装 MCP SDK
```bash
npm install @modelcontextprotocol/sdk
```

### Step 2：写一个简单的 MCP Server
```typescript
// mcp-server.ts
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

const server = new Server({
  name: 'fde-demo-server',
  version: '1.0.0'
}, {
  capabilities: {
    tools: {}
  }
});

// 注册一个工具：查询广州天气
server.setRequestHandler('tools/list', async () => ({
  tools: [{
    name: 'get_weather',
    description: '查询指定城市的天气',
    inputSchema: {
      type: 'object',
      properties: {
        city: { type: 'string', description: '城市名' }
      },
      required: ['city']
    }
  }]
}));

server.setRequestHandler('tools/call', async (request) => {
  if (request.params.name === 'get_weather') {
    const city = request.params.arguments.city;
    // 调用真实 API...
    return {
      content: [{ type: 'text', text: `${city}今天晴，25-32°C` }]
    };
  }
  throw new Error('Tool not found');
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

### Step 3：在 Cursor / Claude Desktop 配置
```json
// ~/.config/claude_desktop_config.json
{
  "mcpServers": {
    "fde-demo": {
      "command": "node",
      "args": ["/path/to/mcp-server.ts"]
    }
  }
}
```

### Step 4：让 AI Agent 直接调用
> 用户：「广州今天天气怎么样？」
> AI：（自动调用 get_weather 工具）广州今天晴，25-32°C

## 🌟 2026 年 MCP 生态 Top 10

1. **GitHub MCP** - 读 Issues / PR / Repo
2. **Figma MCP** - 读设计稿、生成代码
3. **Notion MCP** - 读文档、写文档
4. **PostgreSQL MCP** - 直连数据库、SQL 生成
5. **Playwright MCP** - 浏览器自动化测试
6. **Puppeteer MCP** - 网页抓取
7. **Filesystem MCP** - 文件读写
8. **Slack MCP** - 消息推送
9. **Linear MCP** - 任务管理
10. **Sentry MCP** - 错误监控

## 💼 FDE 工程师的 MCP 学习路径

| 阶段 | 时长 | 内容 |
|---|---|---|
| 入门 | 1 天 | 理解 MCP 协议原理，读完官方文档 |
| 实操 | 3 天 | 写 3 个自定义 MCP Server |
| 进阶 | 1 周 | 集成到企业项目 + 安全审计 |
| 商业 | 2 周 | 为公司 SaaS 产品开发官方 MCP Server |

## ⚠️ 安全红线

1. **永远不要让 MCP 直接操作生产数据库**（必须经过审计层）
2. **API Key 必须放在环境变量**，不要硬编码
3. **敏感操作（删除、支付）必须二次确认**

---

📅 **明日预告**：用 MCP 给 MaxKB 写一个「学生问答智能体」全流程