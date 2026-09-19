/**
 * GET /api/dl-course/chapters
 *
 * 返回 9 章课程详情（章节名 / 时长 / 核心概念 / 推荐资料）
 */

const fs = require('fs');
const path = require('path');

// 引入主课程数据
const dlCourse = require('./dl-course');

// 提取 chapters 字段
const CHAPTERS = dlCourse.COURSE_DATA.chapters;

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', 'https://taoj2025.github.io');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Cache-Control', 'public, max-age=3600');

    if (req.method === 'OPTIONS') return res.status(200).end();
    if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

    return res.status(200).json({
        total: CHAPTERS.length,
        totalHours: CHAPTERS.reduce((sum, c) => sum + c.hours, 0),
        chapters: CHAPTERS,
    });
};