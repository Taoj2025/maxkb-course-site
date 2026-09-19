/**
 * GET /api/dl-course/videos
 *
 * 返回 3 集抖音短视频链接（EP1/2/3 · 60s · 带字幕）
 */

const dlCourse = require('./dl-course');
const VIDEOS = dlCourse.COURSE_DATA.videos;

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', 'https://taoj2025.github.io');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Cache-Control', 'public, max-age=3600');

    if (req.method === 'OPTIONS') return res.status(200).end();
    if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

    return res.status(200).json({
        total: VIDEOS.length,
        totalDuration: VIDEOS.reduce((sum, v) => sum + v.duration, 0),
        videos: VIDEOS,
    });
};