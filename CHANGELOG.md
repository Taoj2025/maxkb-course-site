# MaxKB 课程站 · Changelog

## [Unreleased]

### Added
- ✨ **GitHub Release Workflow**（`.github/workflows/release.yml`）
  - 自动创建 GitHub Release（带变更日志）
  - 推送到远程服务器 119.91.234.159:2222
  - Server酱微信通知
  - 继承现有 `deploy-backend.yml` 配置
- ✨ **CHANGELOG.md** · 变更日志沉淀

### Workflow
- ✅ 复用 `deploy-backend.yml`（硬编码 IP 119.91.234.159）
- ✅ 复用 `deploy.yml`（GitHub Pages 自动部署）
- ✅ 新增 `release.yml`（tag 触发的 Release 流程）

---

## [v2.0.0] - 2026-09-11 - 商业化大版本 🎉

### Added
- ✨ 后端：Node.js + Express + PostgreSQL（9 张表 · bcrypt + JWT · 限流）
- ✨ 前端：6 大 SaaS 组件（信任条 / 数据大字报 / Logo 墙 / 证言 / 对比表 / FAQ / CTA）
- ✨ 新增 4 商业化页面：客户案例 (`cases.html`) / 企业服务 (`enterprise.html`) / 讲师介绍 (`about.html`) / 预约演示
- ✨ 资源下载：基于 `/api/download/:slug` 真实鉴权 + 流式代理
- ✨ 部署：Docker Compose + Nginx 反代 + Let's Encrypt + GitHub Actions 自动部署

### Security
- 🔒 trust proxy + Helmet + bcrypt(10) + JWT 7d + 限流 + CORS 白名单

### Changed
- 🔧 域名切换：maxkb-edu.com → taotaoedu.ltd
- 🔧 全站去除真名"陶建敏"，统一称呼"小陶老师"

---

## [v1.0.0] - 2026-07-27 - FDE 教学站首发

### Added
- ✨ 完整 8 章节课程体系
- ✨ 紫色 AI 科技风首页
- ✨ 管理员后台（JWT 鉴权）
- ✨ articles.json 14 篇文章
- ✨ GitHub Actions deploy.yml（GitHub Pages 自动部署）
- ✨ 自定义域名 maxkb-edu.com

### Core Tech Stack
- Frontend：原生 HTML/CSS/JS（轻量）
- Storage：articles.json（只读）+ PostgreSQL（动态）
- Auth：JWT HS256 + PBKDF2
- Deploy：GitHub Pages + Vercel Functions（API 层）

---

## 格式保护铁律（重要！）

按事实红线⑯ + 第⑱条主动授权 + 第⑲条诚实标注：

| 文件 | 状态 | 处理方式 |
|------|------|---------|
| `articles.json` | 🔒 **只读** | AI 仅做辅助打磨，不覆盖 |
| `admin.html` | 🔒 **只读** | AI 仅做辅助打磨，不覆盖 |
| `index.html` | ⚠️ 谨慎 | 仅追加功能，不破坏现有结构 |
| `*.md`（articles/） | ✅ 可改 | 教学场景增量内容 |
| `*.html`（业务页） | ✅ 可改 | 业务场景增量内容 |
| `.github/workflows/*` | ✅ 可改 | 工作流持续演进 |

升级路径：**新增文件 + 修改文件清单**（不覆盖保护文件）。

---

## 工作流架构

```
main 分支
  ├─ push 触发 deploy.yml → GitHub Pages 自动部署
  ├─ push (backend/**) 触发 deploy-backend.yml → 远程服务器部署
  └─ tag v*.*.* 触发 release.yml → GitHub Release + 远程同步
```

---

*Changelog 版本：v2.0.0+ · 启用：2026-09-19 · 状态：与 GitHub Releases 自动同步*
*生成工具：小Q（AI 协作整理） · 底本：格式保护铁律 + 主动授权⑱*