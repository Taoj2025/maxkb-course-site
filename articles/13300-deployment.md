---
id: 13300
title: "MaxKB 安装部署完整指南"
date: 2026-07-24
tags: ["部署指南"]
summary: "从 0 到 1 全流程 · 4 种部署方式 · 30 分钟跑通企业级 AI 平台"
---

# 🚀 MaxKB 安装部署完整指南

## 📦 部署方式 4 选 1

1. **Docker Compose（推荐）**：5 分钟启动，单机测试
2. **1Panel 应用商店**：10 分钟，集成 Nginx + 数据库
3. **Kubernetes Helm**：30 分钟，生产级集群
4. **源码部署**：60 分钟，二次开发定制

## 🐳 Docker Compose 部署步骤

**前置条件**：
- Linux 服务器（Ubuntu 22.04 / CentOS 7+）
- Docker 24+ · Docker Compose 2.x
- 4 核 CPU + 8GB 内存 + 50GB 磁盘

```bash
# Step 1：拉取镜像
docker pull 1panel/maxkb

# Step 2：创建工作目录
mkdir -p /opt/maxkb && cd /opt/maxkb
mkdir -p {data,logs,postgresql,redis}

# Step 3：启动服务
docker-compose up -d
```

**Step 4**：浏览器打开 `http://your-server-ip:8080`，默认账号 `admin / maxkb123`

## 🔧 常见问题排查

**Q：8080 端口被占用？**
A：修改 docker-compose.yml 端口为 8888 或其他可用端口

**Q：数据库连接失败？**
A：检查 DB_PASSWORD 是否与 PostgreSQL 一致

**Q：忘记 admin 密码？**
A：`docker exec -it maxkb bash` 进入容器，运行 `python manage.py changepassword admin`

👉 [完整部署文档（含 K8s / 1Panel）](https://taoj2025.github.io/maxkb-course-site/)
