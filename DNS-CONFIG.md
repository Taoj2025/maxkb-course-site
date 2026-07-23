# maxkb-edu.com DNS 解析配置（购买后立即执行）

> **作者**：小 Q 为小陶老师定制 · 2026-07-23 22:40
> **域名**：maxkb-edu.com · 腾讯云 / DNSPod

---

## 🎯 完成后效果

- ✅ 用户访问 `https://maxkb-edu.com` 自动看到 MaxKB FDE 教学网站
- ✅ 用户访问 `https://www.maxkb-edu.com` 也自动重定向
- ✅ HTTPS 自动签发（GitHub Pages）
- ✅ 全球 CDN 加速（GitHub CDN）

---

## 📋 DNS 解析配置（5 分钟）

### 在腾讯云 DNSPod 控制台

1. 打开 https://console.dnspod.cn/
2. 进入「我的域名」→ `maxkb-edu.com`
3. 点击「解析」标签

### 添加 5 条记录

```
┌────────────────────────────────────────────────────────────────┐
│ 主机记录  │ 记录类型 │ 记录值                  │ TTL │
├────────────────────────────────────────────────────────────────┤
│ @        │ A        │ 185.199.108.153         │ 600 │
│ @        │ A        │ 185.199.109.153         │ 600 │
│ @        │ A        │ 185.199.110.153         │ 600 │
│ @        │ A        │ 185.199.111.153         │ 600 │
│ www      │ CNAME    │ taoj2025.github.io.     │ 600 │
└────────────────────────────────────────────────────────────────┘
```

### 关键说明

- **A 记录**：4 个 GitHub Pages 的 IP，指向 GitHub 服务器
- **CNAME 记录**：www 子域名指向 taoj2025.github.io
- **TTL 600**：缓存时间 10 分钟（生效更快）

---

## ⚙️ GitHub Pages Custom Domain 配置（3 分钟）

### 在 GitHub 仓库设置

1. 打开 https://github.com/Taoj2025/maxkb-course-site/settings/pages
2. 在「Custom domain」输入框填：`maxkb-edu.com`
3. 点击「Save」
4. 勾选「Enforce HTTPS」
5. 等待 GitHub 验证 DNS（5-30 分钟）

---

## ✅ 验证测试

### 命令行验证

```bash
# 域名解析测试
nslookup maxkb-edu.com
# 应返回 185.199.108.153 等 IP

# HTTPS 访问测试
curl -I https://maxkb-edu.com
# 应返回 HTTP 200
```

### 浏览器验证

打开 https://maxkb-edu.com 应该看到 MaxKB FDE 教学网站

### HTTPS 锁标志

地址栏应有 🔒 锁标志（HTTPS 证书已签发）

---

## 🆘 故障排查

### Q1：DNS 不生效？
A：在腾讯云检查 4 条 A 记录是否正确，等待 30 分钟以上

### Q2：GitHub 显示 "Domain verification failed"？
A：检查 DNS 是否生效（命令：nslookup maxkb-edu.com）

### Q3：HTTPS 灰色锁？
A：在 GitHub Pages 设置里重新勾选「Enforce HTTPS」，等待证书签发（5-30 分钟）

### Q4：访问 404？
A：检查仓库根目录的 `CNAME` 文件是否包含 `maxkb-edu.com`（已配置）

---

## 📞 任何问题

随时联系小 Q！

---

*生成时间：2026-07-23 22:40 · 由 AI 小 Q 为小陶老师定制*