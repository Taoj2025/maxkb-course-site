# MaxKB FDE 教学资料包 · 一站式交付

> **授课教师**：小陶老师（陶建敏）· 广州华商学院
> **生成时间**：2026 年 7 月 23 日
> **用途**：暑期 FDE 培训 · 面向师生（学生 + 同行教师）
> **AI 辅助设计**：小 Q 自动生成

---

## 📦 一站式 ZIP 交付清单

| 类别 | 文件 | 大小 |
|------|------|------|
| 📘 教学讲义 | `docs/MaxKB_FDE教学讲义_小陶老师.docx` | 46 KB |
| 🎨 教学 PPT | `ppt/MaxKB_FDE教学课件_小陶老师.pptx` | 495 KB / **60 页** |
| 💻 源码注释 | `code/maxkb_core_modules.py` | 8 个核心模块 |
| 🖼️ 配图素材 | `images/*.png` | 6 张高质量配图 |
| 📄 项目说明 | `README.md` (本文件) | - |
| 📦 **总 ZIP 包** | `MaxKB_FDE教学资料_v1.0.zip` | ~600 KB |

---

## 🚀 快速开始（学员 30 分钟路径）

1. **环境准备**（5 分钟）
   - 安装 Docker Desktop
   - 申请 DeepSeek API Key

2. **部署 MaxKB**（5 分钟）
   ```bash
   docker run -d --name=maxkb -p 8080:8080 \
     -v ~/.maxkb:/opt/maxkb 1panel/maxkb
   ```

3. **登录 Web 控制台**（2 分钟）
   - http://localhost:8080
   - 用户名 admin / 密码 MaxKB@123..

4. **完成 3 个实验**（共 5.5 小时）
   - 实验 1：Hello MaxKB（30 分钟）
   - 实验 2：知识库问答系统（2 小时）
   - 实验 3：工作流编排（3 小时）

5. **交付实战项目**（可选 · 8 小时）
   - 选 5 大场景之一，3-5 人小组协作
   - 提交 ZIP 一站式交付包

---

## 📂 目录结构

```
MaxKB教学案例/
├── README.md                                  # 项目说明（本文件）
├── docs/
│   ├── MaxKB_FDE教学讲义_小陶老师.docx        # 主讲义（46 KB · 8 章）
│   └── gen_word.py                            # 生成脚本
├── ppt/
│   ├── MaxKB_FDE教学课件_小陶老师.pptx        # 主 PPT（60 页 · 495 KB）
│   ├── helpers.py                             # PPT 工具函数
│   └── gen_*.py                               # 分段生成脚本
├── code/
│   └── maxkb_core_modules.py                  # 8 模块源码注释
└── images/
    ├── 01_五维能力雷达图.png                  # 6 张 PPT 配图
    ├── 02_RAG原理流程图.png
    ├── 03_工作流编排.png
    ├── 04_三层架构图.png
    ├── 05_MCP工具生态.png
    └── 06_五大场景对比.png
```

---

## 📘 教学讲义 8 章节大纲

| 章节 | 标题 | 学时 |
|------|------|------|
| 第 1 章 | 课程概述 · FDE 培训定位 | 0.5h |
| 第 2 章 | 环境准备 · Docker 与模型 API | 1h |
| 第 3 章 | 理论精讲 · RAG / LangChain / Workflow / MCP | 4h |
| 第 4 章 | 实操手册 · 6 步端到端落地 | 4h |
| 第 5 章 | 案例库 · 5 大企业真实场景 | 2h |
| 第 6 章 | 实验指导 · 3 个动手实验 | 5.5h |
| 第 7 章 | 考核方式 · 平时 + 期末 | 1h |
| 第 8 章 | 附录 · 资源与排坑 | 0.5h |
| **合计** | | **18h** |

---

## 🎨 PPT 60 页结构

### PART 0 · 开场（P01-P05 · 5 页）
- P01 封面
- P02 系列课定位
- P03 课程目标 · 三栖产出
- P04 受众定位
- P05 课前引导

### PART 1 · 理论基座（P06-P20 · 15 页）
- P07 MaxKB 是什么 / P08 核心架构 / P09 五维能力
- P10 RAG 原理 / P11 RAG vs 传统 / P12 RAG 代码
- P13 向量化与 pgvector / P14 嵌入代码
- P15 LangChain / P16 模型中立
- P17 Workflow / P18 MCP / P19 Agent 范式 / P20 技术栈剖析

### PART 2 · 实操（P21-P45 · 25 页）
- P21 PART 2 章节封面
- P22-P27 6 步部署链路（Docker / 模型 / 知识库 / 文档 / 应用 / 发布）
- P28 6 步闭环可视化
- P29-P32 工作流节点 / 代码节点 / MCP
- P33 6 大最佳实践 / P34 排坑指南
- P35 现场成果 / P36 中场休息
- P37 调试指标 / P38 调优 6 招 / P39 调试技巧 / P40 JSON
- P41 多模态 / P42 安全权限 / P43 监控日志
- P44 多路召回 / P45 PART 2 总结

### PART 3 · 场景落地（P46-P55 · 10 页）
- P46 PART 3 章节封面 / P47 5 大场景矩阵图
- P48-P52 5 大场景详解（高校客服 / 教师备课 / 文献精读 / 企业知识库 / 医院导诊）
- P53 场景选择决策树 / P54 FDE 落地方程
- P55 现场成果演示

### PART 4 · 收尾（P57-P60 · 5 页）
- P57 PART 4 章节封面 / P58 实验回顾与实战营
- P59 系列课下周预告 / P60 致谢 + 二维码

---

## 💻 源码 8 大核心模块

| 模块 | 路径 | 功能 |
|------|------|------|
| 1 | `apps/application/views.py` | 应用 API 视图层 |
| 2 | `apps/knowledge/chat_pipeline.py` | RAG Pipeline 核心 |
| 3 | `apps/knowledge/handle/document_handler.py` | 文档处理管道 |
| 4 | `apps/workflow/engine.py` | 工作流执行引擎 |
| 5 | `apps/tools/mcp/client.py` | MCP 协议客户端 |
| 6 | `apps/models/model_provider.py` | 模型中立接入层 |
| 7 | `apps/embedding/models/` | Embedding & 向量化 |
| 8 | `ui/src/views/application/` | 前端 Vue 组件 |

---

## 🎯 三大核心原则（贯穿全部材料）

### 1. 严格事实红线
- ✅ 全部内容基于 MaxKB 官方文档与开源源码
- ✅ 不编造未提供的功能、数据、用户数
- ✅ 版本号引用 v1.0·v2.0，统一管理

### 2. 真实案例驱动
- ✅ 5 大企业场景全部给出 ROI 数据
- ✅ 教师备课场景对接 SKC4073 课程
- ✅ 文献精读场景对接 YOLO 课题组

### 3. 一次性 ZIP 打包
- ✅ 教学 PPT + 讲义 + 源码 + 配图 + README 四件套齐全
- ✅ 无需学员自行查找资料
- ✅ 微信一键送达

---

## 🛠️ 技术栈与依赖

| 维度 | 工具 | 版本 |
|------|------|------|
| 文档生成 | python-docx | 1.2.0 |
| PPT 生成 | python-pptx | 1.0.2 |
| 配图生成 | matplotlib + numpy | - |
| 源代码 | Python | 3.12+ |
| 运行环境 | Docker | 24+ |
| MaxKB | 1Panel-dev/MaxKB | v2.0 |

---

## 🎓 教师使用建议

### 学时分配（18 学时）
| 模块 | 学时 | 备注 |
|------|------|------|
| 理论讲解 | 4h | PART 1 |
| 实操演示 | 2h | PART 2 上半 |
| 实验课 | 5.5h | 3 个实验 |
| 场景案例 | 2h | PART 3 |
| 期末项目 | 4h | 学生演示 + 答辩 |
| 答疑 | 0.5h | - |

### 学生交付物清单
- 实验 1 截图 + 应用 ID
- 实验 2 JSON 配置 + 10 题测试报告
- 实验 3 工作流 JSON + 截图
- 期末项目 ZIP 包（含 PPT + 文档 + 截图 + 演示视频）

---

## 📞 联系方式与资源

- 📚 官方文档：https://maxkb.cn/docs/v2/
- 💻 源码仓库：https://github.com/1Panel-dev/MaxKB
- 🐳 Docker Hub：https://hub.docker.com/r/1panel/maxkb
- 👤 教师微信：小陶老师
- 🏫 单位：广州华商学院

---

## 📝 版本信息

| 版本 | 日期 | 状态 |
|------|------|------|
| v1.0 | 2026-07-23 | ✅ 初版交付（PPT 60 页 + 讲义 174 段 + 8 模块源码） |

---

**生成完毕 · 2026 年 7 月 23 日 19:30 GMT+8**
**by 小 Q 为小陶老师定制**
