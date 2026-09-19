/**
 * GET /api/dl-course/experiments
 *
 * 返回 7 大实验详情（实验名 / 学时 / 难度 / GPU 配置）
 */

const dlCourse = require('./dl-course');
const EXPERIMENTS = dlCourse.COURSE_DATA.experiments;

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', 'https://taoj2025.github.io');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Cache-Control', 'public, max-age=3600');

    if (req.method === 'OPTIONS') return res.status(200).end();
    if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

    return res.status(200).json({
        total: EXPERIMENTS.length,
        totalHours: EXPERIMENTS.reduce((sum, e) => sum + e.hours, 0),
        byTier: {
            verified: EXPERIMENTS.filter(e => e.tier === 'verified'),
            comprehensive: EXPERIMENTS.filter(e => e.tier === 'comprehensive'),
            design: EXPERIMENTS.filter(e => e.tier === 'design'),
        },
        experiments: EXPERIMENTS,
    });
};