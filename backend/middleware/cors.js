const origins = (process.env.CORS_ORIGINS || '')
  .split(',')
  .map(s => s.trim())
  .filter(Boolean);

export const corsOptions = {
  origin(origin, cb) {
    // 同源请求（origin 为空，如 curl / 同站）放行
    if (!origin) return cb(null, true);
    if (origins.includes(origin)) return cb(null, true);
    // 开发模式放行所有
    if (process.env.NODE_ENV !== 'production') return cb(null, true);
    cb(new Error('CORS blocked: ' + origin));
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
};
