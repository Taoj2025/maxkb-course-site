/**
 * 统一错误处理
 */
export function errorHandler(err, req, res, _next) {
  console.error('[error]', req.method, req.path, err.message);
  const status = err.status || 500;
  res.status(status).json({
    error: err.message || 'Internal Server Error',
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack }),
  });
}

export function notFoundHandler(req, res) {
  res.status(404).json({ error: 'Not Found', path: req.path });
}
