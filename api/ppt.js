/**
 * GET /api/dl-course/ppt
 *
 * 返回 18 页 PPT 下载链接（紫色 AI 科技风 · 可商用）
 */

const dlCourse = require('./dl-course');
const PPT = dlCourse.COURSE_DATA.ppt;

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', 'https://taoj2025.github.io');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Cache-Control', 'public, max-age=3600');

    if (req.method === 'OPTIONS') return res.status(200).end();
    if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

    return res.status(200).json(PPT);
};