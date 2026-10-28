# taotaoedu.ltd DNS 解析配置

> **最后更新**：2026-10-29
> **域名**：taotaoedu.ltd · 腾讯云 / DNSPod
> **现状**：主站已经**不再走 GitHub Pages**，而是部署在国内服务器 `119.91.234.159`
> 的 nginx 上（证书由 certbot 签发）。GitHub Pages 只剩一个作用 —— 老地址
> `taoj2025.github.io/maxkb-course-site/` 会 301 跳到主站，是个跳板。

---

## 🎯 完成后效果

- ✅ 用户访问 `https://taotaoedu.ltd` 自动看到 MaxKB FDE 教学网站
- ✅ 用户访问 `https://www.taotaoedu.ltd` 也看到同一个站（同一份 nginx 配置）
- ✅ HTTPS 自动签发（Let's Encrypt，certbot 续期）
- ✅ `v.taotaoedu.ltd` 指向 Vercel 快照站（国内备用线路 / 加速用）

---

## 📋 DNS 解析配置

### 在腾讯云 DNSPod 控制台

1. 打开 https://console.dnspod.cn/
2. 进入「我的域名」→ `taotaoedu.ltd`
3. 点击「解析」标签

### 当前生效的记录

```
┌────────────────────────────────────────────────────────────────┐
│ 主机记录  │ 记录类型 │ 记录值                  │ TTL │
├────────────────────────────────────────────────────────────────┤
│ @        │ A        │ 119.91.234.159          │ 600 │
│ www      │ A        │ 119.91.234.159          │ 600 │
│ v        │ CNAME    │ cname.vercel-dns.com.  │ 600 │
└────────────────────────────────────────────────────────────────┘
```

### 关键说明

- **A 记录**：指向国内服务器，nginx 接管 `taotaoedu.ltd` 和 `www.taotaoedu.ltd`
  （两个域名写在同一个 `server_name` 块里，所以一条 A 记录 + 复制一条给 www 就行）
- **`v` 的 CNAME**：Vercel 快照站。`*.vercel.app` 在国内被 DNS 污染 + SNI 过滤
  三重拦截，**不能用**，所以挂自己的子域名。注意是 `cname.vercel-dns.com`，
  不是 `vercel-dns.com` 也不是 `cname.vercel.app`
- **TTL 600**：缓存时间 10 分钟（生效更快）

---

## ⚙️ Vercel 侧需要同步做的事

DNS 指过去还不够，Vercel 项目也得认这个域名，否则它不签证书：

1. Vercel 控制台 → 项目 `maxkb-course-site-bk10` → **Settings → Domains**
2. 添加 `v.taotaoedu.ltd`
3. 等 Vercel 自动签发证书（一般 1-5 分钟）

验证（在**国内服务器**上跑才有意义 —— 国内才是关键视角）：

```bash
bash scripts/verify-custom-domain.sh v.taotaoedu.ltd
```

会查 DNS 指向、TLS 证书签发方、多段 `/api/*` 路径、内容与源站是否一致、
付费墙有没有被绕过，一共五组。

---

## ✅ 验证测试

### 命令行验证

```bash
# 域名解析测试
nslookup taotaoedu.ltd
# 应返回 119.91.234.159

# HTTPS 访问测试
curl -I https://taotaoedu.ltd
# 应返回 HTTP 200
```

### 浏览器验证

打开 https://taotaoedu.ltd 应该看到 MaxKB FDE 教学网站

### HTTPS 锁标志

地址栏应有 🔒 锁标志（HTTPS 证书已签发）

---

## 🆘 故障排查

### Q1：DNS 不生效？
A：在腾讯云检查 A 记录是否正确，等待 30 分钟以上。改完 DNS 可以先
`nslookup taotaoedu.ltd` 确认解析已经变了。

### Q2：HTTPS 灰色锁 / 证书报错？
A：证书是在**服务器**上签的，不是 GitHub 签的。查服务器上的
`/etc/nginx/sites-available/maxkb-api` 里的证书路径，和 certbot 的续期配置。

### Q3：访问 404？
A：主站的 web root 是 `/var/www/maxkb-course-site`（一个 git clone）。
在服务器上 `git pull` 一下就是最新的 —— 主站**提交即生效**，不用等 CI。

### Q4：`v.taotaoedu.ltd` 打不开？
A：多半是 Vercel 那边还没加这个域名，或者 DNS 记录没生效。
先跑 `scripts/verify-custom-domain.sh` 看是哪一环断了。

---

## 📞 任何问题

随时联系小 Q！
