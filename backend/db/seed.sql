-- ==========================================================
-- MaxKB 教学站 · 种子数据
-- 管理员密码由 scripts/init-admin.js 用 bcrypt 重置
-- 文章正文由 scripts/import-articles.js 从 articles/*.md 灌入
-- ==========================================================

-- 管理员占位（密码占位串，后续 init-admin.js 会覆盖为 bcrypt 哈希）
INSERT INTO users (email, password_hash, role, plan_id)
VALUES ('2949465671@qq.com', '__INIT_VIA_SCRIPT__', 'admin', 'flagship')
ON CONFLICT (email) DO NOTHING;

-- 8 个课程章节（迁移自 assets/js/data.js）
INSERT INTO chapters (id, title, description, icon, tag, duration, pages, outputs, sort_order) VALUES
(1, '课程概述 · FDE 培训定位',           '理解 MaxKB 在企业 AI 落地中的位置与价值，掌握 18 学时学习路径。', '🎯', 'theory',   '0.5h', 'P01-P05', ARRAY['学习路径图','课时分配表'],                  10),
(2, '环境准备 · Docker 与模型 API',      '硬件选型、Docker 安装、模型 API 申请，确保本地环境就绪。',     '🔧', 'practice', '1h',   'P22-P24', ARRAY['本地 MaxKB 启动','API Key 就绪'],           20),
(3, 'RAG · 检索增强生成原理',             '从 0 到 1 理解 RAG 范式，掌握召回 / 重排 / 生成三大核心。',     '🔍', 'theory',   '1h',   'P10-P14', ARRAY['RAG 原理图','代码示例'],                     30),
(4, 'LangChain · LLM 应用框架',          '掌握 LangChain 6 大组件，理解 MaxKB 在 LangChain 之上的封装。', '🔗', 'theory',   '1h',   'P15-P16', ARRAY['6 组件卡片','模型中立说明'],                  40),
(5, 'Workflow · 可视化工作流',           '拖拽节点编排复杂业务，从 Prompt 到 Agent 的渐进式升级。',       '⚙️', 'practice', '1.5h', 'P17,P29-P32', ARRAY['工作流设计模式','JSON 示例'],          50),
(6, 'MCP · 模型上下文协议',               '理解 2024 年开源协议，让 LLM 调用任意外部系统。',              '🔌', 'theory',   '1h',   'P18',     ARRAY['MCP 生态图','接入实战'],                      60),
(7, '6 步实操 · 端到端落地',              'Docker 部署 → 模型接入 → 知识库 → 应用调试 → 发布嵌入，全流程实战。', '🚀', 'practice', '4h', 'P22-P27', ARRAY['6 步闭环图','截图证据'],                  70),
(8, '5 大企业场景 · FDE 落地',            '高校客服 / 教师备课 / 文献精读 / 企业知识库 / 医院导诊，均含真实 ROI。', '🏢', 'scene', '2h', 'P46-P55', ARRAY['场景矩阵图','ROI 对比'],                  80)
ON CONFLICT (id) DO NOTHING;
SELECT setval('chapters_id_seq', 8, true);

-- 6 个资源（与 downloads/ 文件名一致）
INSERT INTO resources (slug, title, description, file_size, min_plan) VALUES
('r_a1b2c3d4.docx',                     'MaxKB FDE 教学讲义',     '8 章节精讲 Word 讲义 · 46 KB',                          47092,   'standard'),
('r_e5f6g7h8.pptx',                     'MaxKB FDE 教学课件',     '60 页紫色 AI 科技风 PPT · 495 KB',                      506489,  'standard'),
('r_i9j0k1l2.py',                       'MaxKB 核心模块源码',     '8 大核心模块 Python 源码 · 500+ 行',                    19385,   'standard'),
('r_m3n4o5p6.md',                       'README',                 '完整使用说明 · 免费',                                   7183,    'free'),
('MaxKB_FDE教学资料_v1.0_小陶老师.zip', '总压缩包',               '完整教学资料 · 1.8 MB',                                 1791715, 'standard'),
('images.zip',                          '教学配图包',             '6 张高清配图 · 355 KB',                                 355379,  'standard')
ON CONFLICT (slug) DO NOTHING;

-- 14 篇文章元数据（正文后续 import-articles.js 灌入）
INSERT INTO articles (slug, title, summary, category, tags, color, published_at) VALUES
('13297-course-intro',                'MaxKB FDE 教学课程介绍',                                  '基于开源 MaxKB（1Panel-dev）的企业级智能体平台教学，60 页 PPT + 8 章讲义 + 500+ 行源码',                    '课程介绍',  ARRAY['课程介绍','MaxKB'],           'purple',         '2026-07-23'),
('13298-scenarios',                   '5 大 MaxKB 应用场景实战 ROI 案例',                        '高校客服 ROI 1:8 · 教师备课 1:6 · 文献精读 1:15 · 企业知识库 1:12 · 医院导诊 1:10',                    '实战案例',  ARRAY['实战案例','ROI'],             'blue',           '2026-07-23'),
('13299-faq',                         'MaxKB FDE 课程学员常见问题 FAQ',                          '10 个高频问题 · 课程难度 / 学习路径 / 资料获取 / 实战项目 / 就业方向',                                  '学员FAQ',   ARRAY['学员FAQ'],                    'success-green',  '2026-07-23'),
('13300-deployment',                  'MaxKB 安装部署完整指南',                                  '从 0 到 1 全流程 · 4 种部署方式 · 30 分钟跑通企业级 AI 平台',                                          '部署指南',  ARRAY['部署指南'],                    'orange',         '2026-07-24'),
('13301-knowledge-base',              '企业知识库构建 4 大要点',                                 '文档切片策略 / 向量化模型选择 / 检索优化 / 持续运营 4 大关键',                                         '知识库',    ARRAY['知识库'],                      'purple',         '2026-07-24'),
('13302-agent-workflow',              'Agent 工作流设计实战案例',                                '单 Agent / 多 Agent / 工具调用 / 任务分解 4 大模式 + 完整代码',                                         'Agent',     ARRAY['Agent'],                       'blue',           '2026-07-24'),
('13303-teacher-course-prep',         '教师如何用 MaxKB 备课',                                   '教师专属场景 · 5 步备课法 · 学科知识库构建 · 学生答疑机器人',                                            '教师专属',  ARRAY['教师专属'],                    'success-green',  '2026-07-24'),
('13304-student-projects',            '学员项目展示与点评',                                       'SKC4073 / SKC7423 / SKC7773 三门课程 · 5 位同学优秀作品 · 教师点评',                                  '学员作品',  ARRAY['学员作品'],                    'warning-yellow', '2026-07-24'),
('13305-ai-frontend-agent',           'AI Agent 重塑前端开发：FDE 的下一个 3 年',                 'GitHub Copilot Workspace + Cursor Composer + Vercel v0 · 三大 AI 前端 Agent 横评 · FDE 工程师能力模型重塑',  '最新动态',  ARRAY['FDE前沿','AI Agent'],          'purple',         '2026-07-27'),
('13306-vercel-edge-2026',            'Vercel 2026 边缘计算新特性：FDE 部署成本直降 80%',       'Vercel Edge Functions + ISR 2.0 + Fluid Compute · 三件套让部署成本暴降 · 真实案例数据',                   '最新动态',  ARRAY['FDE前沿','Vercel'],            'blue',           '2026-07-27'),
('13307-mcp-protocol-frontend',       'MCP 协议在前端的落地：让 AI Agent 安全调用你的 API',       'Model Context Protocol 入门到实战 · 5 分钟给前端项目接入 MCP Server · 真实可运行代码',                  '最新动态',  ARRAY['FDE前沿','MCP'],               'purple',         '2026-07-27'),
('13308-edge-runtime-ssr-comparison', 'Edge Runtime vs SSR vs SSG：2026 年前端渲染方案终极对决', '三大渲染方案性能/成本/SEO 全维度对比 · 2026 年选型决策树 · Next.js 15 + Hono 实战',                       '最新动态',  ARRAY['FDE前沿','前端架构'],          'orange',         '2026-07-27'),
('13309-fde-job-market-2026',         '2026 年 FDE 就业市场报告：AI 时代前端工程师的真实薪资',     'BOSS 直聘 + 拉勾 + LinkedIn 三平台数据 · FDE 薪资分布 · 5 类高薪技能 · 转岗路径',                       '最新动态',  ARRAY['FDE前沿','就业市场'],          'success-green',  '2026-07-27'),
('13310-vercel-edge-functions-fde',   '⚡ Vercel Edge Functions 完全实战指南：从 Serverless 到 Fluid Compute', '2026 Vercel Functions 5 大核心能力 + 3 种 Runtime 选型 + Region 配置 + 性能对比 + FDE 5 步实战', '最新动态',  ARRAY['Vercel','Edge Functions','Serverless','FDE','Fluid Compute','边缘计算'], 'blue', '2026-07-27')
ON CONFLICT (slug) DO NOTHING;
