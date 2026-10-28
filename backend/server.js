import 'dotenv/config';
import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import morgan from 'morgan';
import rateLimit from 'express-rate-limit';

import { corsOptions } from './middleware/cors.js';
import { errorHandler, notFoundHandler } from './middleware/error.js';

import authRouter      from './routes/auth.js';
import articlesRouter  from './routes/articles.js';
import chaptersRouter  from './routes/chapters.js';
import contactRouter   from './routes/contact.js';
import aihotRouter     from './routes/aihot.js';
import resourcesRouter from './routes/resources.js';
import downloadRouter  from './routes/download.js';
import dlCourseRouter from './routes/dl-course.js';
import adminRouter     from './routes/admin.js';

const app = express();

// 信任 Nginx 反代（1层），让 req.ip / req.secure 正确
app.set('trust proxy', 1);

app.use(helmet({ crossOriginResourcePolicy: false }));
app.use(cors(corsOptions));
app.use(express.json({ limit: '1mb' }));
app.use(morgan(process.env.NODE_ENV === 'production' ? 'combined' : 'dev'));

// 限流：登录 / 注册 / 联系表单
const authLimiter    = rateLimit({ windowMs: 60_000, max: 20, message: { error: '请求过于频繁，请稍后再试' } });
const registerLimiter = rateLimit({ windowMs: 60_000, max: 5,  message: { error: '注册请求过于频繁' } });
const contactLimiter = rateLimit({ windowMs: 60_000, max: 10, message: { error: '提交过于频繁，请稍后再试' } });

app.use('/api/auth/login',    authLimiter);
app.use('/api/auth/register', registerLimiter);
app.use('/api/contact',       contactLimiter);

// 健康检查
app.get('/api/health', (_req, res) => res.json({ ok: true, ts: Date.now() }));

// 业务路由
app.use('/api/auth',      authRouter);
app.use('/api/articles',  articlesRouter);
app.use('/api/chapters',  chaptersRouter);
app.use('/api/contact',   contactRouter);
app.use('/api/aihot',     aihotRouter);
app.use('/api/resources', resourcesRouter);
app.use('/api/download',  downloadRouter);
app.use('/api/dl-course', dlCourseRouter);
app.use('/api/admin',     adminRouter);

app.use(notFoundHandler);
app.use(errorHandler);

const port = process.env.PORT || 3001;
// 监听地址：默认 0.0.0.0（Docker 容器内必须如此，否则宿主机反代连不上）；
// 生产环境直接跑在主机上时用 HOST=127.0.0.1 收窄到本机，只允许 Nginx 反代接入。
const host = process.env.HOST || '0.0.0.0';
app.listen(port, host, () => {
  console.log(`🚀 MaxKB backend listening on http://${host}:${port}`);
  console.log(`   NODE_ENV=${process.env.NODE_ENV || 'development'}`);
});
