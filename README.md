# MaxKB FDE 教学网站

> 基于 1Panel-dev/MaxKB 的开源企业级智能体平台教学课程
> 紫色 AI 科技风 · FDE 实战导向 · 师生混合受众

## 🌐 访问地址

部署到 GitHub Pages 后可访问：
```
https://<GitHub用户名>.github.io/maxkb-course-site/
```

## 🔥 最新 FDE 前沿资讯（2026-07-27 重大升级）

独立动态栏目·每日 8:00 自动抓取更新:
- 页面地址: https://taoj2025.github.io/maxkb-course-site/latest.html
- **AI 热点实时聚合**：调用 [aihot-news-skill](https://clawhub.ai) 抓取 [aihot.virxact.com](https://aihot.virxact.com) RSS · 50 条最新 AI 行业热点
- **搜索 + 类别筛选**：所有类别 / 行业动态 / 技巧观点 / AI 产品 / AI 模型 / 论文
- **4 路数据源**：AIHOT (50+) · GitHub Trending · Hacker News (buzzing.cc) · InfoQ/36kr
- 每日 5 篇精选文章 + AI 重写 + 自动审核 + 自动发布
- 已收录 5 篇种子文章（AI Agent / Vercel Edge / MCP 协议 / Edge Runtime / FDE 就业）

### 实时聚合模块架构

```
latest.html (前端 UI)
  ├─ data/aihot.json       (38792 bytes · 50 条原始热点)
  ├─ data/aihot-fde.json   (32863 bytes · 42 条 FDE 筛选后)
  └─ articles.json         (5 篇精选"最新动态"类目)
```

## 📚 课程内容

- **理论基座**（PART 1）：MaxKB / RAG / LangChain / Workflow / MCP / Agent
- **6 步实操**（PART 2）：Docker 部署 → 模型接入 → 知识库 → 应用调试 → 发布嵌入
- **5 大场景**（PART 3）：高校客服 / 教师备课 / 文献精读 / 企业知识库 / 医院导诊

## 🎯 目标受众

- 学生：1 周搭出可演示项目
- 同行教师：把 AI 落地到自己的课程/班级
- 企业项目：交付客服/HR/导诊等垂直场景

## 🛠️ 技术栈

- HTML5 + CSS3 + Vanilla JavaScript（无框架）
- 紫色 AI 科技风（#5B2EBF 主色）+ 紫色→蓝色→红色渐变（最新动态页）
- 响应式布局（PC / Pad / 手机自适应）
- **GitHub Pages** + **GitHub Contents API**（无需后端服务器）
- **articles.json** 动态内容 + **article.html** 同时支持 `?id=` 和 `?slug=` 双参数
- **Formspree** 留言 / **Giscus** 评论 / **Supabase** 会员（即将启用）
- **admin.html** + SHA-256 哈希的本地鉴权

## 🚀 本地预览

```bash
cd site
python3 -m http.server 8000
# 浏览器访问 http://localhost:8000
```

## 📦 部署到 GitHub Pages

### 方式一：自动部署（推荐）

1. Fork / 创建本仓库
2. 推送代码到 main 分支
3. 仓库 Settings → Pages
4. Source 选择 "GitHub Actions"
5. 自动触发 `.github/workflows/deploy.yml`

### 方式二：手动部署

1. 仓库 Settings → Pages
2. Source 选择 "Deploy from a branch"
3. Branch 选择 `main` / `(root)`

## 📂 目录结构

```
site/
├── index.html                     # 主页面（6 区块）
├── latest.html                    # 🔥 最新 FDE 前沿资讯（v2 7月27日升级）
│                                  #    · AI 热点实时聚合模块
│                                  #    · 5 篇精选文章 + 4 数据源状态
├── article.html                   # 文章详情页（支持 ?id= / ?slug= 双参数）
├── membership.html                # 会员方案页
├── user.html                      # 个人中心页
├── admin.html                     # 管理员后台（SHA-256 哈希登录）
├── faq.html                       # 常见问题页
├── articles.json                  # 文章元数据（13 篇·含"最新动态" 5 篇）
├── articles/                      # Markdown 文章 13 篇
│   ├── 13305-ai-frontend-agent.md
│   ├── 13306-vercel-edge-2026.md
│   ├── 13307-mcp-protocol-frontend.md
│   ├── 13308-edge-runtime-ssr-comparison.md
│   └── 13309-fde-job-market-2026.md
├── data/                          # ✨ 新增：AI 热点数据源
│   ├── aihot.json                 # 50 条 AI 热点（38792 bytes）
│   └── aihot-fde.json             # 42 条 FDE 筛选版（32863 bytes）
├── scripts/fde-daily/             # 自动化抓取脚本
│   └── fetch_articles.py          # RSSHub 多源抓取（已在 GitHub Actions 排队）
├── assets/
│   ├── css/style.css              # 紫色 AI 科技风样式
│   ├── js/data.js                 # 课程数据
│   ├── js/script.js               # 交互脚本
│   └── js/membership.js           # 会员管理（localStorage + btoa）
├── downloads/                     # 教学资料下载
│   ├── MaxKB_FDE教学讲义_小陶老师.docx
│   ├── MaxKB_FDE教学课件_小陶老师.pptx
│   ├── maxkb_core_modules.py
│   ├── images.zip
│   └── MaxKB_FDE教学资料_v1.0.zip
├── .github/workflows/deploy.yml   # 自动部署
├── .nojekyll                       # 禁用 Jekyll
├── sitemap.xml                     # 站点地图（含 latest.html）
└── README.md
```

## 📞 联系

- 教师：小陶老师（陶建敏）
- 单位：广州 · 大数据专业
- 开源项目：https://github.com/1Panel-dev/MaxKB

## 📄 协议

本课程资料基于 **GPL v3** 开源，可自由用于教学。
MaxKB 项目本身基于 GPL v3 协议。

---

由 AI 小 Q 辅助设计 · 最后更新：2026 年 7 月 27 日

### 版本历史
- **v1.1 (2026-07-27)** · latest.html v2：嵌入 aihot-news-skill 爬虫 + 50 条实时热点 + 搜索 + 类别筛选；数据源全面升级
- **v1.0 (2026-07-23)** · 站点正式上线 + 5 篇精选文章 + 5 资源权限拦截 + admin.html + 会员 MVP
- **v0.9 (2026-07-16)** · 设计语言「紫色 AI 科技风」定型 + 27 页 PART 骨架