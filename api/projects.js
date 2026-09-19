/**
 * GET /api/dl-course/projects
 *
 * 返回学生实战项目集（医疗 / 自动驾驶 / 电商客服 3 大场景）
 */

const dlCourse = require('./dl-course');
const PROJECTS = dlCourse.COURSE_DATA.projects;

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', 'https://taoj2025.github.io');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Cache-Control', 'public, max-age=3600');

    if (req.method === 'OPTIONS') return res.status(200).end();
    if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

    return res.status(200).json({
        total: PROJECTS.length,
        projects: PROJECTS,
    });
};