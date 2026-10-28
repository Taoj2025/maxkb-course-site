import { Router } from 'express';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { COURSE_DATA } from '../data/dl-course.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// 下载目录（和 routes/download.js 保持一致）
const DOWNLOADS_DIR = process.env.DOWNLOADS_DIR
  ? path.resolve(process.env.DOWNLOADS_DIR)
  : path.resolve(__dirname, '../../downloads');

const r = Router();

const { meta, chapters, experiments, projects, videos, ppt, tools, grading } = COURSE_DATA;

/**
 * 课件/短视频这类素材是「计划中」的文件：页面上一直挂着下载按钮，
 * 但文件未必已经上传到服务器。这里如实告诉前端到底存不存在，
 * 免得用户点下去只看到一个 404。
 */
function assetInfo(url) {
  const name = url ? decodeURIComponent(url.split('/').pop()) : null;
  if (!name) return { file: null, available: false };
  const exists = fs.existsSync(path.join(DOWNLOADS_DIR, name));
  return { file: name, available: exists };
}

// GET /api/dl-course —— SKC5053 课程完整数据
r.get('/', (req, res) => {
  res.json(COURSE_DATA);
});

// GET /api/dl-course/chapters —— 9 章课程详情
r.get('/chapters', (req, res) => {
  res.json({
    total: chapters.length,
    totalHours: chapters.reduce((sum, c) => sum + (c.hours || 0), 0),
    chapters,
  });
});

// GET /api/dl-course/experiments —— 7 大实验详情
r.get('/experiments', (req, res) => {
  res.json({
    total: experiments.length,
    totalHours: experiments.reduce((sum, e) => sum + (e.hours || 0), 0),
    byTier: {
      verified: experiments.filter((e) => e.tier === 'verified'),
      comprehensive: experiments.filter((e) => e.tier === 'comprehensive'),
      design: experiments.filter((e) => e.tier === 'design'),
    },
    experiments,
  });
});

// GET /api/dl-course/projects —— 学生实战项目集
r.get('/projects', (req, res) => {
  res.json({
    total: projects.length,
    projects,
  });
});

// GET /api/dl-course/videos —— 3 集短视频链接
r.get('/videos', (req, res) => {
  res.json({
    total: videos.length,
    totalDuration: videos.reduce((sum, v) => sum + (v.duration || 0), 0),
    videos: videos.map((v) => ({ ...v, ...assetInfo(v.url) })),
  });
});

// GET /api/dl-course/ppt —— 课件信息与下载地址
r.get('/ppt', (req, res) => {
  res.json({ ...ppt, ...assetInfo(ppt.downloadUrl) });
});

// GET /api/dl-course/meta —— 课程基本信息 + 工具链与评分方式
r.get('/meta', (req, res) => {
  res.json({ meta, tools, grading });
});

export default r;
