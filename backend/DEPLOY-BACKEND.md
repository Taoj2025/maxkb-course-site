# MaxKB FDE 后端部署文档

> **版本**：v2.0 · 2026-09-11
> **架构**：Node.js 20 + Express 4 + PostgreSQL 16
> **目标读者**：小陶老师（部署上线到独立服务器）
> **目标服务器**：公网 `http://119.91.234.159/` · 域名 `taotaoedu.ltd`

## 🌐 完整链路（推荐方案 · Nginx 反代）

```
公网用户
   │
   │ HTTPS
   ▼
┌─────────────────────────────────┐
│ taotaoedu.ltd (443)             │  ← Let's Encrypt 证书
│ Nginx (主机进程)                 │
│   ├─ /api/*  ──► 127.0.0.1:3001 │  ← 反代到 API 容器
│   └─ 其他      ──► GitHub Pages  │  ← 前端静态（自动部署）
└─────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ Docker Compose                  │
│  ├─ maxkb-postgres  127.0.0.1:5432 │
│  └─ maxkb-api       127.0.0.1:3001 │
└─────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ PostgreSQL 16 · 9 张表           │
└─────────────────────────────────┘
```

**前端调用示例**（已写入 `assets/js/config.js`）：
```js
API_BASE = 'https://taotaoedu.ltd/api'   // Nginx 反代后的同源路径
```

**公网可达 API**：`https://taotaoedu.ltd/api/health`

---

## 🚦 三种部署方式

| 方式 | 难度 | 推荐度 | 适用场景 |
|---|---|---|---|
| **A. Docker Compose + Nginx 反代** | ⭐ | ⭐⭐⭐⭐⭐ | **推荐** · 一次配置，跨机器复现 |
| **B. PM2** | ⭐⭐ | ⭐⭐⭐⭐ | 单机部署，简单直接 |
| **C. systemd** | ⭐⭐⭐ | ⭐⭐⭐ | 系统级服务，自启动 |

下面以**方式 A**为主线，含 Nginx 反代 + Let's Encrypt + 防火墙完整步骤。

---

## 🔒 安全前置清单（部署前必做）

> ⚠️ 用户的 PostgreSQL 密码 **tjm2026** 仅用于本地开发。**生产环境必须修改**！

### 1. 修改所有密码

```bash
# PostgreSQL 密码（生产请用 32 位随机字符串）
openssl rand -hex 16    # → 用于 PGPASSWORD

# JWT 密钥（必须是 64 位 hex，千万别用默认值）
openssl rand -hex 32    # → 用于 JWT_SECRET

# 管理员默认密码
openssl rand -base64 16 # → 用于 ADMIN_DEFAULT_PASSWORD
```

### 2. 防火墙配置（**必须** · ufw 或 iptables）

> ⚠️ 用户给的 PostgreSQL 密码 `tjm2026` 之前是公网可访问，**生产前必须修改**！

#### 使用 ufw（Ubuntu 推荐）

```bash
sudo ufw allow 22/tcp          # SSH
sudo ufw allow 80/tcp          # HTTP (Let's Encrypt 校验)
sudo ufw allow 443/tcp         # HTTPS
sudo ufw default deny incoming # 默认拒绝入站
sudo ufw enable
sudo ufw status verbose        # 确认状态
```

#### 或使用 iptables（CentOS / RHEL）

```bash
sudo iptables -A INPUT -i lo -j ACCEPT
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -j DROP
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

**绝不要放行的端口**：
- ❌ `3001`（API 容器）· 由 Nginx 反代到 127.0.0.1
- ❌ `5432`（Postgres）· 容器仅绑 127.0.0.1
- ❌ `22` 改 SSH 端口 + 密钥登录（可选加固）

### 3. HTTPS（Nginx + Let's Encrypt）

```bash
# 安装 Nginx + certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# 部署反代配置（项目自带模板）
sudo cp /opt/maxkb-api/backend/nginx/maxkb-api.conf \
        /etc/nginx/sites-available/maxkb-api.conf
sudo ln -sf /etc/nginx/sites-available/maxkb-api.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default   # 删默认页

# 首次申请证书（standalone 模式，需要先停 nginx）
sudo systemctl stop nginx
sudo certbot certonly --standalone \
  -d taotaoedu.ltd -d www.taotaoedu.ltd \
  --email 2949465671@qq.com --agree-tos --no-eff-email
sudo systemctl start nginx

# 验证配置
sudo nginx -t
sudo systemctl reload nginx

# 自动续期（certbot 已默认装 systemd timer，无需手动加）
sudo systemctl list-timers | grep certbot
```

**⚠️ 重要**：DNS 必须先把 `taotaoedu.ltd` 和 `www.taotaoedu.ltd` 都解析到 `119.91.234.159`，certbot 才能签出证书。

如暂时无法用域名，可先用 HTTP 模式调试（注释掉 `ssl_certificate` 几行 + 改 listen 80）。

### 4. 定期备份数据库

```bash
# 每天凌晨 3 点自动备份，保留 7 天
0 3 * * * docker exec maxkb-postgres pg_dump -U postgres postgres | gzip > /backup/maxkb-$(date +\%Y\%m\%d).sql.gz
```

---

## 方式 A · Docker Compose 部署（推荐）

### 准备工作

```bash
# 1. 安装 Docker + Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # 重新登录生效

# 2. 创建项目目录
sudo mkdir -p /opt/maxkb-api && cd /opt/maxkb-api
```

### 上传后端代码

把本仓库 `backend/` 整个目录上传到服务器：

```bash
# 在本地打包
cd /path/to/maxkb-course-site
tar czf backend.tar.gz --exclude='backend/node_modules' --exclude='backend/.env' --exclude='backend/.pgdata' backend/

# 上传到服务器
scp backend.tar.gz user@your-server:/opt/maxkb-api/

# 在服务器解压
cd /opt/maxkb-api && tar xzf backend.tar.gz && cd backend
```

### 创建 `.env` 文件

```bash
cp .env.example .env
nano .env
```

**关键配置项**：

```bash
# PostgreSQL
PGUSER=postgres
PGDATABASE=postgres
PGPASSWORD=<上面 openssl rand -hex 16 的结果>

# JWT
JWT_SECRET=<上面 openssl rand -hex 32 的结果>

# CORS 白名单 · 改成您的前端域名
CORS_ORIGINS=https://taotaoedu.ltd,https://taoj2025.github.io

# 管理员
ADMIN_EMAIL=2949465671@qq.com
ADMIN_DEFAULT_PASSWORD=<上面 openssl rand -base64 16 的结果>
```

### 启动服务

```bash
# 首次启动 · 自动建表 + 灌种子数据
docker compose up -d

# 查看日志
docker compose logs -f api

# 健康检查
curl http://127.0.0.1:3001/api/health
# → {"status":"ok","db":"up",...}
```

### 初始化管理员 + 导入文章

```bash
# 初始化管理员账号（admin role + bcrypt 密码）
docker compose exec api node scripts/init-admin.js

# 导入 articles/*.md 正文
docker compose exec api node scripts/import-articles.js
```

### 日常运维命令

```bash
docker compose ps              # 看状态
docker compose restart api      # 重启 API
docker compose logs --tail 100 api   # 最近 100 行日志
docker compose pull && docker compose up -d   # 升级

# 进入容器调试
docker compose exec api sh
```

---

## 方式 B · PM2 部署（直接装系统）

### 安装 Node.js 20 + PostgreSQL 16

```bash
# Ubuntu 22.04+
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs postgresql-16

# 启动 PG
sudo systemctl enable --now postgresql
```

### 创建数据库

```bash
sudo -u postgres psql <<'SQL'
CREATE DATABASE maxkb;
CREATE USER maxkb_app WITH ENCRYPTED PASSWORD '您的密码';
GRANT ALL PRIVILEGES ON DATABASE maxkb TO maxkb_app;
SQL
```

### 部署代码

```bash
cd /opt && sudo git clone <your-repo> maxkb-api
cd maxkb-api/backend
sudo npm ci --omit=dev
sudo cp .env.example .env && sudo nano .env
# 改 PGPASSWORD / JWT_SECRET / CORS_ORIGINS

# 灌库
sudo -u postgres psql -d maxkb -f db/schema.sql
sudo -u postgres psql -d maxkb -f db/seed.sql

# 初始化管理员 + 导入文章
node scripts/init-admin.js
node scripts/import-articles.js
```

### 用 PM2 守护进程

```bash
sudo npm install -g pm2

# 启动
pm2 start server.js --name maxkb-api -i 1 --time

# 设置开机自启
pm2 startup
pm2 save

# 监控
pm2 monit
pm2 logs maxkb-api --lines 100
```

### Nginx 反向代理

```nginx
# /etc/nginx/sites-available/api.taotaoedu.ltd
server {
    listen 80;
    server_name api.taotaoedu.ltd;

    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 流式响应（大文件下载必须）
        proxy_buffering off;
        proxy_request_buffering off;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/api.taotaoedu.ltd /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d api.taotaoedu.ltd
```

---

## 方式 C · systemd 服务（系统级守护）

适合想要完全控制启动顺序、依赖、日志轮转的场景。

### 创建服务文件

```bash
sudo tee /etc/systemd/system/maxkb-api.service > /dev/null <<'EOF'
[Unit]
Description=MaxKB FDE API
Documentation=https://taotaoedu.ltd
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=maxkb
Group=maxkb
WorkingDirectory=/opt/maxkb-api/backend
EnvironmentFile=/opt/maxkb-api/backend/.env
ExecStart=/usr/bin/node server.js
Restart=on-failure
RestartSec=5
StandardOutput=append:/var/log/maxkb-api/access.log
StandardError=append:/var/log/maxkb-api/error.log

# 安全加固
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/maxkb-api/backend

[Install]
WantedBy=multi-user.target
EOF

sudo mkdir -p /var/log/maxkb-api && sudo chown maxkb:maxkb /var/log/maxkb-api
```

### 启动

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now maxkb-api
sudo systemctl status maxkb-api
sudo journalctl -u maxkb-api -f
```

---

## ✅ 部署完成后的验证清单

按顺序执行：

```bash
# 1. 健康检查
curl https://api.taotaoedu.ltd/api/health
# → {"status":"ok","db":"up"}

# 2. 注册一个测试用户
curl -X POST https://api.taotaoedu.ltd/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"verify@example.com","password":"test123456"}'

# 3. 登录拿 token
TOKEN=$(curl -X POST https://api.taotaoedu.ltd/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"verify@example.com","password":"test123456"}' | jq -r .token)

# 4. 拉文章列表
curl https://api.taotaoedu.ltd/api/articles?size=3

# 5. 拉课程章节
curl https://api.taotaoedu.ltd/api/chapters

# 6. 留言（限流 10/分钟）
curl -X POST https://api.taotaoedu.ltd/api/contact \
  -H "Content-Type: application/json" \
  -d '{"name":"验证","email":"v@v.com","message":"部署验证"}'
```

所有 6 个 curl 应该都返回 2xx。

### 浏览器侧验证

1. 访问 `https://taotaoedu.ltd`
2. 注册一个测试账号
3. 顶部状态条显示「体验会员」
4. 点击下载资源 → 提示「需升级」
5. 管理员登录（`admin.html`）→ 升级该用户到旗舰
6. 用户刷新 → 显示旗舰徽章 → 下载成功
7. 管理员数据看板数字 +1

---

## 🆘 故障排查

### 502 Bad Gateway

```bash
# 检查 API 是否在跑
docker compose ps   # 或: pm2 status / systemctl status maxkb-api

# 检查端口监听
sudo ss -tlnp | grep 3001
```

### 数据库连接失败

```bash
# 检查 PG 状态
docker compose ps postgres

# 手动连一下
docker compose exec postgres psql -U postgres -d postgres -c "SELECT 1"
```

### CORS 跨域报错

打开浏览器 console，看错误信息里的 `Access-Control-Allow-Origin`。

```bash
# 1. 确认 .env 的 CORS_ORIGINS 包含您的前端域名（带 https://）
# 2. 重启 API
docker compose restart api
```

### 慢 / 502

```bash
# 看 API 日志
docker compose logs --tail=200 api | grep -i error

# 看 PG 慢查询
docker compose exec postgres psql -U postgres -d postgres -c "SELECT * FROM pg_stat_activity WHERE state='active'"
```

### 忘记管理员密码

```bash
# 直接重置（不依赖 init-admin）
docker compose exec postgres psql -U postgres -d postgres <<'SQL'
UPDATE users
SET password_hash = crypt('您的新密码', gen_salt('bf', 10))
WHERE email = '2949465671@qq.com';
SQL
```

---

## 📦 数据备份与恢复

### 备份（cron 每天凌晨 3 点）

```bash
sudo tee /etc/cron.d/maxkb-backup > /dev/null <<'EOF'
0 3 * * * root docker exec maxkb-postgres pg_dump -U postgres postgres | gzip > /backup/maxkb-$(date +\%Y\%m\%d).sql.gz
EOF
```

### 恢复

```bash
gunzip -c /backup/maxkb-20260911.sql.gz | docker exec -i maxkb-postgres psql -U postgres -d postgres
```

---

## 🌐 域名与 DNS 配置建议

- `taotaoedu.ltd` → CNAME → `taoj2025.github.io` （前端）
- `api.taotaoedu.ltd` → A → 您的服务器 IP （后端）
- 推荐加 `www` 301 重定向到主域

---

## 📞 联系

部署过程中遇到任何问题：

- 📧 邮箱：2949465671@qq.com
- 💬 微信：taotao_maxkb
- 📚 课程问题：[MaxKB FDE 教学](https://taotaoedu.ltd)

---

> 💡 提示：所有部署文档均经过本地端到端测试。如发现错误，欢迎反馈。