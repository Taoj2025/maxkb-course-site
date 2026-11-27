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
npm run deploy:alias                                 # 把别名指到这次部署（见坑四）
```

> ⚠️ **只在 HTML 外壳改了才需要部署。**
> `data/` `articles/` `articles.json` 走 rewrites 实时回源站
> （内容机器人推完就生效），Vercel 静态快照里根本没有这些文件。
> 每次内容更新都部署 Vercel = 白烧 Hobby 的每日 100 次配额（坑五）。

> ⚠️ **国内网络要设代理**。`api.vercel.com` 直连会偶发连接超时，
> Node 的 fetch 默认不认 `HTTP(S)_PROXY`：
> ```bash
> export HTTPS_PROXY=http://127.0.0.1:8086 HTTP_PROXY=http://127.0.0.1:8086
> ```
> `scripts/assign-vercel-alias.mjs` 会自己检测代理变量并带上
> `--use-env-proxy` 重新拉起（Node 24 才有这个开关）。

部署后验证：

```bash
npm run verify:deploy -- v.taotaoedu.ltd             # 多段 API 路径、POST 体、部署指纹
bash scripts/verify-custom-domain.sh v.taotaoedu.ltd  # 国内服务器上跑，五组检查
```

> ⚠️ `vercel --prod` 成功 **不等于** 线上换版本了。
> 一定要跟着跑 `npm run deploy:alias`（坑四），再跑验证脚本。

---

## 四个会静默失败的坑

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

> 每次 `git push` 之后，Vercel 的 Git 集成也会自己试着部署一次，
> 那一次**一定是 BLOCKED**（同一个检查拦的）——这是正常的，不用管。
> 真正生效的是 CLI 部署（`vercel --prod`）出来的那次 READY 部署，
> 再配上 `npm run deploy:alias` 把别名指过去。

两个修法：

1. **让仓库的提交作者邮箱 = Vercel 账号已验证的邮箱**（现在用的就是这个）
2. 在 Vercel 账号里验证 `taojianmin@jc2009.com`
   （Account Settings → Emails），这样机器人以外的作者也能部署

### 坑四：别名不一定会自己跟过去（最阴的一个）

Vercel 给每次 production 部署挂一个 `deployment-alias` 检查。
**这次部署可以是 READY、构建成功、sha 都对，但这个检查卡在 `pending`** ——
别名压根没动，线上跑的还是上一次（甚至是十天前）的部署。

2026-10-29 实测：部署 `dpl_GNV8adw...` 状态 READY、构建日志里
`proxy.js` 编译成功、静态快照也生成了，但
`GET /v4/aliases/v.taotaoedu.ltd` 指向的还是 `dpl_5vdQfht6...`（10-28 的老部署）。

线上表现（首页照常打开，从页面上完全看不出没更新）：

| 请求 | 老部署 | 新部署应有的结果 |
|---|---|---|
| `/build-info.json` | 404 | 200 + 部署指纹 |
| `/api/health` | 200（老部署的 `api/[...path].js`，只匹配单段） | 200（走中间件） |
| `/api/dl-course/chapters` | **404** | 200（多段路径必须走中间件） |

**所以每次部署完必须显式指一次别名，并核对它真的动了：**

```bash
npm run deploy:alias
```

脚本会：找出最新的 READY production 部署 → 把所有别名
（`v.taotaoedu.ltd` + 两个 `*.vercel.app`）指过去 → 再逐个查回来核对指向。
核对不过就退出码 1。

别名是可逆的 —— 重新指回旧部署就是回滚。

`vercel inspect` 看不出这个问题（它显示的是这次部署自己的配置，
不是线上实际在跑的那次）。

### 坑五：Hobby 每天 100 次部署配额（团队级，两个项目一起算）

Hobby 计划的部署上限是**每天 100 次**，而且是**整个团队共用**的 ——
不是每个项目各 100。超了报：

```
Resource is limited - try again in 24 hours
(more than 100, code: "api-deployments-free-per-day")
```

配额是**滚动 24 小时窗口**，不是每天零点清零。

**这个站的坑在于：内容机器人每 30 分钟推一次**（`aihot` + `jobs` 两路 cron），
每次 push 都触发一次 Vercel 自动部署 —— 一天就是 **90+ 次**，
刚好顶到上限。更糟的是当时仓库里还留着重复项目
`maxkb-course-site-bk9`，**它连着同一个 GitHub 仓库**，
所以每次 push 部署两次 —— 配额瞬间打满。

**排查方法**（看谁在吃配额）：

```bash
# 团队级部署列表，按小时/项目数
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v6/deployments?teamId=$TEAM_ID&limit=100" \
  | python -c "
import json,sys,collections
d=json.load(sys.stdin)['deployments']
print(collections.Counter(x['name'] for x in d))
"
```

**修法（2026-11-28 实施）**：

1. **删掉重复项目** `maxkb-course-site-bk9` —— 它没有任何域名，
   只是建站过程中留下的废弃项目，却占着一半配额。
2. **关掉两个项目的 GitHub 自动部署**（`DELETE /v9/projects/{id}/link`）。
   站点是「静态快照 + 实时转发」架构：`data/` `articles/` 走 rewrites
   回源站，**内容更新根本不需要重新部署 Vercel** —— 只有 HTML 外壳改了才需要。
   自动部署纯属白烧配额。
3. 以后**只在 HTML 外壳改动时手动部署**：
   `vercel --prod` → `npm run deploy:alias`。

> ⚠️ 关掉自动部署后，**别名不会自己跟过去**了（这本来就是坑四）。
> 每次部署完必须跑 `npm run deploy:alias`。

### 坑六：Supabase 集成被暂停 → 所有部署 BUILD_FAILED

2026-11-05 起，**每一次**部署都失败，报：

```
BUILD_FAILED / Resource provisioning failed
```

看着像构建问题，其实是**集成资源 provision 失败**：
项目上挂着一个 Supabase 集成（Marketplace），
而那个 Supabase 项目已经被暂停了 —— Vercel 每次部署都要先 provision 它，
provision 不回来，部署就整体失败。

**根因在 `integrations` 字段里**（`vercel inspect` 看不出来）：

```bash
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v13/deployments/{id}" | python -c "
import json,sys
d=json.load(sys.stdin)
print(d.get('errorCode'), d.get('errorMessage'))
print('integrations:', d.get('integrations'))   # status: error
"
```

**修法**：这个站的前后端**根本没用 Supabase**（数据库是源站自建 PostgreSQL，
前端只调 `/api/*`）。直接把集成资源从项目上摘掉：

```bash
# 断开连接（不删除 Supabase 项目本身）
curl -X DELETE -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v1/storage/stores/{storeId}/connections/{connectionId}?teamId=$TEAM_ID"
```

断开后：集成 provision 不再是部署的前置条件 → 部署恢复 READY。
对应的 `*_SUPABASE_*` 环境变量也会一并清掉（前端本来就不读）。

---

## 部署指纹

静态快照基本不变时，从页面上分不出线上是新是旧部署。
`scripts/build-vercel-site.sh` 会产出 `site/build-info.json`：

```bash
curl -s https://<域名>/build-info.json
# {"sha":"583a905","builtAt":"2026-10-29T06:15:41Z"}
```

拉一下就知道线上跑的是哪一次构建。

> ⚠️ 取 sha 要用 `VERCEL_GIT_COMMIT_SHA`，不能用 `git rev-parse` ——
> Vercel 的构建机里没有 `.git` 目录，`git rev-parse` 一定失败，
> 指纹会永远是 `"unknown"`（`npm run check:vercel` 现在会查这条）。

---

## 其它

### `headers` 数组是「后写的覆盖先写的」

`vercel.json` 里每条 `headers` 规则都会生成一条带 `continue: true` 的路由，
**同一个 header key 被多条规则命中时，靠后的那条赢**。

所以通用规则必须放在前面、具体规则放后面：

```jsonc
{ "source": "/assets/(.*)",          "Cache-Control": "public, max-age=3600" },   // 兜底
{ "source": "/assets/js/vendor/(.*)", "Cache-Control": "public, max-age=2592000" }, // 30 天
{ "source": "/assets/images/(.*)",    "Cache-Control": "public, max-age=2592000" }  // 30 天
```

反过来的话，兜底规则在最后，
`/assets/js/vendor/marked.min.js` 只会拿到 1 小时缓存（2026-10-29 实测过）。

---

## 目录里有什么

- `site/` 是构建产物，不进仓库（`.gitignore`）
- `articles/` `articles.json` `data/` `downloads/` **不在快照里**，
  走 `vercel.json` 的 rewrites 实时转发源站 ——
  尤其 `downloads/` 必须回源，付费墙（nginx 白名单）才拦得住
- `npm run check:vercel` —— 部署前自检
- `npm run test:middleware` —— 打真源站，20 项
