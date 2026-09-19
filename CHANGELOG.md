# Changelog

MaxKB FDE 课程站所有变更记录。

## [Unreleased]

### Added
- ✨ GitHub Release Workflow（`.github/workflows/release.yml`）
  - 自动部署到 GitHub Pages
  - 同步到 Vercel（可选）
  - 同步到远程服务器（可选 rsync）
  - 自动创建 GitHub Release
  - 微信 Server酱通知

## [2026-09-19] - 工作流升级

### Added
- ✨ GitHub Release Workflow（自动部署+远程同步+Release创建）
- ✨ `articles.json` 14 篇文章完整索引
- ✨ `fde-skills.html` v2.0（6 大技能聚类）

### Changed
- 🔧 `fde-jobs.html` v2.0（OpenAI/Anthropic/DeepSeek/Kimi 等 8 家 AI 公司）
- 🔧 `latest.html` 升级（5 篇种子文章）
- 🔧 课程数据 `fde-jobs-2026.json` v2.0

### Security
- 🔒 `articles.json` + `admin.html` 格式保护铁律（只读不覆盖修改）
- 🔒 数据库凭证轮换（用户本地执行）
- 🔒 最小权限 PostgreSQL 角色

## [2026-07-27] - FDE 教学站 v1.0 上线

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

*Changelog 版本：v1.0 · 启用：2026-09-19 · 状态：与 GitHub Releases 自动同步*
*生成工具：小Q（AI 协作整理） · 底本：格式保护铁律 + 主动授权⑱*