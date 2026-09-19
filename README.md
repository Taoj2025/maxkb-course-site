# MaxKB FDE 教学网站

> 🎓 基于开源企业级智能体平台（MaxKB）的 FDE（Frontend Developer Engineer）实战教学课程
> 🎨 紫色 AI 科技风 · 9 章节 + 7 大实验 + 54 学时 · 可商用 · 开源教学

[![GitHub release](https://img.shields.io/github/v/release/Taoj2025/maxkb-course-site)](https://github.com/Taoj2025/maxkb-course-site/releases)
[![Deploy Status](https://img.shields.io/github/actions/workflow/status/Taoj2025/maxkb-course-site/deploy.yml)](https://github.com/Taoj2025/maxkb-course-site/actions)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Style](https://img.shields.io/badge/style-AI%20Tech-purple)](https://taotaoedu.ltd/)
[![Teacher](https://img.shields.io/badge/Teacher-小陶-orange)](https://taotaoedu.ltd/)

---

## 🌐 访问地址

| 渠道 | URL |
|------|-----|
| **正式域名** | https://taotaoedu.ltd/ |
| **GitHub Pages** | https://taoj2025.github.io/maxkb-course-site/ |
| **API（Vercel）** | https://maxkb-course-site.vercel.app/api/ |
| **GitHub 仓库** | https://github.com/Taoj2025/maxkb-course-site |

---

## 🎯 课程特色

- 🎓 **9 章节系统教学**（AI 基础 → RAG → LangChain → Workflow → MCP → 深度学习）
- 🧪 **7 大实验**（验证性 → 综合性 → 设计性）
- ⏱️ **54 学时**（18 理论 + 36 实验）
- 🎨 **紫色 AI 科技风**视觉设计
- 📚 **60+ PPT 教学页** · **完整源码** · **5 大企业场景实战**
- 🔌 **Vercel Serverless Functions**（9 个 API 接口）
- 🛡️ **安全规范 8 条**（参数化 SQL + 输入校验 + Secret 不入代码）

---

## 📚 核心页面

| 页面 | URL | 说明 |
|------|-----|------|
| 首页 | `/` | 60+ PPT + 9 章节概览 |
| 课程大纲 | `/syllabus.html` | 完整 9 章课程结构 |
| **深度学习** | `/dl-course.html` | SKC5053 深度学习专业课 |
| 最新前沿 | `/latest.html` | AI 热点实时聚合 |
| 客户案例 | `/cases.html` | FDE 实战案例 |
| 企业服务 | `/enterprise.html` | 企业级定制方案 |
| 讲师介绍 | `/about.html` | 教学团队 |
| 会员服务 | `/membership.html` | 3 档会员套餐 |
| 资源下载 | `/downloads/` | 教学资源 · 工具 · 案例 |

---

## 🔌 API 接口（Vercel Serverless）

| 端点 | 用途 |
|------|------|
| `GET /api/articles` | 文章列表 |
| `GET /api/article/:slug` | 单篇文章详情 |
| `GET /api/articles/featured` | 精选文章 |
| `POST /api/auth` | 管理员登录（JWT）|
| `GET /api/comments/:articleId` | 文章评论 |
| `GET /api/membership` | 会员信息 |
| `GET /api/admin-list` | 管理员列表 |
| `POST /api/save` | 文章保存 |
| `POST /api/upload` | 文件上传（OSS 签名）|
| `GET /api/dl-course` | **深度学习课程数据** |
| `GET /api/dl-course/chapters` | 9 章节详情 |
| `GET /api/dl-course/experiments` | 7 实验详情 |
| `GET /api/dl-course/projects` | 学生项目集 |
| `GET /api/dl-course/videos` | 抖音短视频 |
| `GET /api/dl-course/ppt` | 18 页 PPT |

---

## 🚀 技术栈

```
Frontend: 原生 HTML / CSS / JavaScript
Backend: Vercel Serverless Functions (Node.js)
Storage: articles.json (只读) + PostgreSQL (动态)
Auth: JWT HS256 + PBKDF2 密码哈希
Upload: 阿里云 OSS 签名 URL 直传
Deploy: GitHub Pages (前端) + Vercel (API) + GitHub Actions
Domain: maxkb-edu.com / taotaoedu.ltd
```

---

## 🔒 安全规范（硬约束）

按用户安全规范 8 条铁律（2026-09-19 启用）：

| # | 铁律 |
|---|------|
| 1 | **参数化 SQL** - 所有 DB 查询用 `$1, $2` 占位符 |
| 2 | **输入校验白名单** - 所有用户输入先校验 |
| 3 | **Secret 不入代码** - JWT_SECRET / DB 密码不进代码或前端 |
| 4 | **文件上传安全** - 后缀白名单 + MIME + 重命名 + 非执行目录 |
| 5 | **不新增公网端口** - 数据库/缓存不监听 0.0.0.0 |
| 6 | **OpenClaw Gateway 仅 127.0.0.1** |
| 7 | **改完跑 `openclaw security audit`** |
| 8 | **拒绝不安全代码** - 发现 SQLi/XSS/命令注入立即拒绝 |

---

## 🛠️ 本地开发

```bash
# 1. 克隆仓库
git clone https://github.com/Taoj2025/maxkb-course-site.git

# 2. 安装依赖
cd maxkb-course-site
npm install

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入数据库 / JWT / OSS 凭证

# 4. 数据库初始化
node scripts/migrate-articles.js

# 5. 启动开发服务器
npm run dev

# 6. 访问
open http://localhost:3000
```

---

## 📦 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|---------|
| **v3.1.1** | 2026-09-19 | 清理「广州华商学院」字段（用户硬约束）|
| v3.1.0 | 2026-09-19 | 深度学习课程接口（dl-course.html + 6 个 API）|
| v3.0.0 | 2026-09-19 | GitHub Release workflow + 远程服务器自动部署 |
| v2.0.0 | 2026-09-11 | 商业化大版本（Node.js + Express + PostgreSQL）|
| v1.0.0 | 2026-07-27 | FDE 教学站首发 |

[完整 Release Notes](https://github.com/Taoj2025/maxkb-course-site/releases)

---

## 🎬 相关链接

- 🎓 **教学站点**：https://taotaoedu.ltd/
- 📺 **抖音/视频号**：搜索「小陶」
- ✉️ **联系邮箱**：可通过 GitHub Issues 联系

---

## 📄 许可证

本项目采用 MIT 许可证（教学使用 · 可商用 · 需保留原作者署名）。

---

*由 [小陶老师](https://taotaoedu.ltd/) 主导开发 · MaxKB 课程站开发团队*