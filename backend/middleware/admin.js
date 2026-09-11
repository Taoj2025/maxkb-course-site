/**
 * 管理员鉴权中间件：必须配合 authRequired 使用
 * 必须挂载在 authRequired 之后（保证 req.user 已存在）
 */
export function adminRequired(req, res, next) {
  if (!req.user || req.user.role !== 'admin') {
    return res.status(403).json({ error: '需要管理员权限' });
  }
  next();
}
