## 🎉 v2.0.0 商业化大版本

> **发布日期**：2026-09-11
> **提交**：2929d71
> **作者**：小陶老师 + Claude Code

---

## 🌟 核心变更

### 🏗️ 真实后端架构（全新）

- **Node.js 20 + Express 4** 全栈后端
- **PostgreSQL 16** 数据库，9 张表设计
- **bcrypt(10)** 密码哈希 + **JWT 7d** 认证
- **Helmet + CORS 白名单 + 限流** 安全加固
- **资源下载鉴权**：基于 `/api/download/:slug` 真实鉴权 + 流式代理
- **Docker Compose** 一键起 Postgres + API

### 🎨 前端商业化升级

新增 **6 大 SaaS 组件**（紫色 AI 科技风 + 商业感）：

- `.trust-bar` 顶部信任徽章条
- `.stat-mega` 数据大字报（800+ 学员 / 50+ 项目）
- `.logo-wall` 客户 Logo 墙
- `.testimonial-grid` 6 张客户证言
- `.comparison-table` 套餐对比表
- `.faq-accordion` 折叠 FAQ
- `.cta-banner` 终极 CTA
- `.case-card` 案例卡片

### 📄 4 个新商业化页面

| 页面 | 内容 |
|---|---|
| `cases.html` | 6 大行业真实案例（高校/教师/文献/企业/医院/政务） |
| `enterprise.html` | 4 大服务模块 + 套餐定价 + 销售表单 |
| `about.html` | 小陶老师时间线 + 团队 + 资质 + 媒体 |
| `trial.html` | 3 种演示类型 + 时段预约 |

### 🔧 重构页面

- `index.html` — 加 5 大商业化 section
- `membership.html` — 3 档定价 + 对比表 + 微信收款 + FAQ
- `admin.html` — 完全重写（去 localStorage → 真实 API + 8 项数据看板 + 操作日志）
- `user.html` — 完全重写（去 localStorage → 真实 `/api/me`）

### 🚀 部署交付

- **Dockerfile** · 非 root 用户 + 健康检查
- **docker-compose.yml** · Postgres + API 一键起，端口仅绑 127.0.0.1
- **Nginx 反代配置** · `maxkb-api.conf` 含 HTTPS + 安全头
- **GitHub Actions 双工作流**
  - `deploy.yml` — 前端部署 GH Pages（路径过滤）
  - `deploy-backend.yml` — 后端 SSH 部署（仅 `backend/**` 变更触发）
- **DEPLOY-BACKEND.md** · Docker / PM2 / systemd 三方式 + 完整安全清单

---

## 📊 变更统计

| 类型 | 数量 |
|---|---|
| 修改文件 | 12 |
| 新增文件 | 29 |
| 后端 JS 文件 | 16（全部 `node --check` 通过）|
| 前端 JS 文件 | 5（全部 `node --check` 通过）|
| 数据库表 | 9 |
| API endpoint | 16 |
| 密码泄漏 | **0** |

---

## 🔐 安全要点

- ✅ PostgreSQL 密码 **不入仓库**（`.env` 已 gitignore）
- ✅ 前端不接触数据库（全部走 `/api/*` + JWT）
- ✅ bcrypt 哈希（DB 内是 `$2b$10$...`）
- ✅ CORS 白名单 + Helmet + rate-limit
- ✅ SSH_PRIVATE_KEY 仅在 GitHub Secrets

---

## 📦 上线路径

1. **DNS**：`taotaoedu.ltd` → `119.91.234.159`
2. **服务器**：参考 `backend/DEPLOY-BACKEND.md`
3. **GitHub Secrets**：`SSH_HOST` / `SSH_USER` / `SSH_PRIVATE_KEY`
4. **首次**：服务器 `git clone` + 创建 `.env` + `docker compose up -d`
5. **自动**：之后 `backend/**` push 自动 SSH 部署

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)