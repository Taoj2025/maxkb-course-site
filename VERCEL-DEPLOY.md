# Vercel 部署指南

> 站点在 Vercel 上是**快照 + 转发层**：静态页面走快照（CDN），`/api/*` 由根目录的
> `proxy.js`（Routing Middleware）转发到源站 `https://taotaoedu.ltd`。
> 后端和数据库始终在自建服务器上，Vercel 不碰生产库。

- 项目：`maxkb-course-site-bk10`（Hobby 团队 `tjmtaotao358-3909s-projects`）
- 正式域名：`https://taotaoedu.ltd`（主站，服务器 nginx）
- 备用线路：`https://v.taotaoedu.ltd`（Vercel，域名需手动在控制台加 + DNSPod 加 CNAME）

---

## 部署步骤

```bash
vercel link --project maxkb-course-site-bk10 --yes   # 关联项目（写 .vercel/project.json）
vercel --prod --yes                                  # 生产部署
```

部署后验证：

```bash
bash scripts/verify-vercel-deploy.sh <域名>          # 多段 API 路径、POST 体、部署指纹
bash scripts/verify-custom-domain.sh v.taotaoedu.ltd  # 国内服务器上跑，五组检查
```

---

## 三个会静默失败的坑

### 坑一：`proxy.entrypoint` 的扩展名必须是 `.js` / `.ts`

写成 `proxy.mjs` 会在部署时被接口直接拒掉：

```
The `proxy.entrypoint` must be a `.js` or `.ts` file path,
or a Python `module:attr`.
```

**表现是「部署不生效」** —— 线上继续跑旧版本，从页面上完全看不出来
（静态快照基本不变时尤其难发现）。2026-10-29 排查这个花了一整轮。

`proxy.js` 里用 ESM 语法（`export const config` / `export default`）没问题，
Vercel 构建时用 esbuild 编成 CommonJS。仓库根 `package.json` 没有 `"type": "module"`，
Node 本地跑时会自动按 ESM 重新解析（有一行 warning，正常）。

`scripts/check-vercel-config.mjs` 现在会检查这条。

### 坑二：`proxy.matcher` 只能配一处

`vercel.json` 的 `proxy.matcher` 和入口文件导出的 `config.matcher` **同时存在**
→ 构建失败 → 部署不换版本。本仓库把 matcher 放在 `vercel.json` 里，
`proxy.js` 里只导出 `runtime`。

### 坑三：提交作者邮箱必须是 Vercel 团队成员的邮箱

项目上有一个 Vercel 内置的 deployment check（`vercel-ci-check`），
production 部署要过它才拿得到 production 别名。判定依据是
**git 提交的作者邮箱**能不能对应到有部署权限的 Vercel 账号。

这个仓库是**私有仓库** + **Hobby 团队** ⇒ 只有 team owner 能部署。
当前情况：

| 提交来源 | 作者邮箱 | 结果 |
|---|---|---|
| 本地（我/小陶老师） | `taojianmin@jc2009.com` | 被拦（该邮箱未在 Vercel 账号上验证） |
| 服务器机器人（AI 热点刷新） | `root@localhost.localdomain` | 被拦 |
| Vercel 账号主邮箱 | `tjmtaotao358@gmail.com` | ✅ 通过 |

被拦时的表现：

```
The deployment was blocked because the commit author doesn't have permission
to create deployments for this project.
```

**注意**：构建其实已经成功了（build 是过的），只是拿不到 production 别名，
所以 `vercel inspect` 里显示的 Routes 是新配置、但线上还是旧的。

两个修法：

1. **让仓库的提交作者邮箱 = Vercel 账号已验证的邮箱**（现在用的就是这个）
2. 在 Vercel 账号里验证 `taojianmin@jc2009.com`
   （Account Settings → Emails），这样机器人以外的作者也能部署

---

## 部署指纹

静态快照基本不变时，从页面上分不出线上是新是旧部署。
`scripts/build-vercel-site.sh` 会产出 `site/build-info.json`：

```bash
curl -s https://<域名>/build-info.json
# {"sha":"862c9bc","builtAt":"2026-10-29T06:20:11Z"}
```

拉一下就知道线上跑的是哪一次构建。

---

## 其它

- `site/` 是构建产物，不进仓库（`.gitignore`）
- `articles/` `articles.json` `data/` `downloads/` **不在快照里**，
  走 `vercel.json` 的 rewrites 实时转发源站 ——
  尤其 `downloads/` 必须回源，付费墙（nginx 白名单）才拦得住
- `npm run check:vercel` —— 部署前自检
- `npm run test:middleware` —— 打真源站，20 项
