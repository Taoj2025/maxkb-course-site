# MaxKB FDE 后端 API · 生产镜像
# 基于 Node.js 20-alpine · ES Modules

FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev --no-audit --no-fund

# ---------- 运行时 ----------
FROM node:20-alpine
WORKDIR /app

# 安全：非 root 用户
RUN addgroup -S maxkb && adduser -S maxkb -G maxkb

# 复制依赖
COPY --from=deps /app/node_modules ./node_modules
COPY package.json ./

# 复制源码
COPY server.js ./
COPY db ./db
COPY middleware ./middleware
COPY routes ./routes
COPY scripts ./scripts

# 下载资料（本地资源代理转发用）
COPY ../downloads ./public-downloads

# 切换非 root 用户
RUN chown -R maxkb:maxkb /app
USER maxkb

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:3001/api/health || exit 1

EXPOSE 3001

# 启动
CMD ["node", "server.js"]