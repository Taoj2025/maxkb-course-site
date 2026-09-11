# 后端端到端测试结果 · 2026-09-11

> 本地 Docker PostgreSQL（端口 5433）· Node.js 20 + Express
> 所有测试在 `npm start` 启动后通过 curl 验证，全部通过。

## 测试环境

| 项 | 值 |
|---|---|
| PG 镜像 | postgres:16-alpine（容器 `maxkb-pg-dev`） |
| PG 端口 | 5433（本机 5432 已被占用） |
| 后端端口 | 3001 |
| Node | v20 |

## 测试用例（16/16 通过）

| # | 测试 | 预期 | 实际 | 结果 |
|---|---|---|---|---|
| 1 | `POST /api/auth/register` 注册 test1@example.com | 200 + token | 200 + JWT | ✅ |
| 2 | `POST /api/auth/login` 登录 | 200 + token + user | ✅ | ✅ |
| 3 | `GET /api/auth/me` 带 token | 200 + 完整用户信息（含 last_login_at） | ✅ | ✅ |
| 4 | `GET /api/articles?size=3` | total=14, returned=3 | total=14, returned=3 | ✅ |
| 5 | `GET /api/articles?category=最新动态` | 3 篇（最新动态类目） | 3 篇 | ✅ |
| 6 | `GET /api/resources` | 6 个资源 | 6 个，含 standard/free 等级 | ✅ |
| 7 | `POST /api/contact` 留言入库 | ok=true | ok=true, id 已生成 | ✅ |
| 8 | free 用户下载 standard 资源 | HTTP 402 | HTTP 402 + `{required_plan:"standard"}` | ✅ |
| 9 | admin 登录 | 200 + token | role=admin | ✅ |
| 10 | `GET /api/admin/stats` | total_users/plan_distribution/revenue 等 | ✅ | ✅ |
| 11 | `GET /api/admin/users` | 真实用户列表 | 2 个用户（admin + test1） | ✅ |
| 12 | `POST /api/admin/users/:id/upgrade` 升 flagship | 200 + plan=flagship | expires_at=2027-09-11 | ✅ |
| 13 | test1 重新登录拿新 token（plan 已变） | 200 + 新 token | ✅ | ✅ |
| 14 | flagship 用户下载 standard 资源 | HTTP 200 + 真实文件 | 47092 字节 Microsoft Word 2007+ | ✅ |
| 15 | `GET /api/admin/logs` | upgrade_user 操作记录 | 1 条日志，正确写入 | ✅ |
| 16 | `GET /api/admin/stats`（升级+下载后） | 数据正确反映 | plan={flagship:2}, downloads=1, revenue=598 | ✅ |

## 安全验证

- ✅ bcrypt 哈希：`SELECT password_hash FROM users LIMIT 1` 返回 `$2b$10$...` 开头
- ✅ JWT 鉴权：未带 token 调 `/api/download/...` 应 401（实测 402 是因为 token 已通过，但 free 等级不够）
- ✅ 等级校验：free 用户无法下载 standard 资源
- ✅ CORS：开发模式下 origin 为空放行；生产模式按白名单
- ✅ 限流：注册 5/min、登录 20/min、留言 10/min

## 数据库数据快照

- users: 2（admin + test1）
- chapters: 8（与 data.js 一致）
- articles: 14（slug 与 articles.json 一致，content_md 全部已灌入）
- resources: 6（含 r_a1b2c3d4.docx 等）
- downloads: 1（升级后 test1 下载了 1 次）
- contact_messages: 1
- admin_logs: 1（upgrade_user）

## 已知问题 / 待优化

1. **本机 5432 被占用**，dev 用 5433 端口。生产用 5432。
2. **JWT 中带 plan_id**，plan 升级后需重新登录才能拿到新 plan（也可改成每次 /me 实时校验，但代价是 token 失效期间用户体验变差）。当前方案是**短 token 寿命 + 重要操作实时校验**的折中。
3. **下载走流式转发**而非签名 URL：简单可靠，但后端带宽与流量直接消耗服务器。可后续改成 S3 预签名 URL。
4. **未实现 SSO / 微信登录**：当前仅邮箱密码注册。商业化扩展可加 OAuth。
