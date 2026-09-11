import jwt from 'jsonwebtoken';

/**
 * JWT 鉴权中间件：解析 Authorization: Bearer <token>
 * 成功后挂载 req.user = { sub, email, role, plan }
 */
export function authRequired(req, res, next) {
  const h = req.headers.authorization || '';
  const token = h.startsWith('Bearer ') ? h.slice(7) : null;
  if (!token) return res.status(401).json({ error: '未登录' });

  try {
    req.user = jwt.verify(token, process.env.JWT_SECRET);
    next();
  } catch (e) {
    return res.status(401).json({ error: 'token 无效或过期' });
  }
}

/**
 * 签发 JWT
 */
export function signToken(user) {
  return jwt.sign(
    {
      sub:  user.id,
      email: user.email,
      role:  user.role  || 'user',
      plan:  user.plan_id || 'free',
    },
    process.env.JWT_SECRET,
    { expiresIn: process.env.JWT_EXPIRES_IN || '7d' }
  );
}
