# Supabase 后端接入完整指南（30-60 分钟）

> **作者**：小 Q 为小陶老师定制 · 2026-07-23 22:40
> **目的**：把 localStorage（假数据库）升级到 Supabase（真云数据库）

---

## 🎯 为什么要升级 Supabase？

### 当前局限
- 用户注册 → 数据存在用户浏览器
- 您管理员后台只能看到「模拟数据」
- 多设备用户需要分别注册
- 用户清理浏览器缓存 = 数据丢失

### Supabase 升级后
- ✅ 真数据库（用户数据上云）
- ✅ 您管理员看到**真实注册列表**
- ✅ 多设备同步（手机/电脑/平板都能登录）
- ✅ 数据永久保存（除非您主动删）
- ✅ 免费层：500MB 数据库 + 50K 用户 + 1GB 文件存储

---

## 🛠️ 第一步：注册 Supabase（3 分钟）

### 操作流程

1. 浏览器打开 https://supabase.com/
2. 点击右上角「Start your project」
3. 用 GitHub 登录（推荐 · 您已有 GitHub 账号）
4. 创建组织：`MaxKB-FDE`（任意名字）
5. 创建项目：
   - Name：`maxkb-course`
   - Database Password：`自动生成强密码 · 请妥善保存`
   - Region：`Northeast Asia (Tokyo)` 或 `Singapore`
   - Plan：`Free`（永久免费）

---

## 📊 第二步：建表 SQL（5 分钟）

### 2.1 进入 SQL Editor

`https://app.supabase.com/project/YOUR_PROJECT_ID/sql`

### 2.2 执行以下 SQL

```sql
-- 1. 用户表
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  plan_id TEXT NOT NULL DEFAULT 'free',  -- free / standard / flagship
  joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  upgraded_at TIMESTAMP WITH TIME ZONE,
  expires_at TIMESTAMP WITH TIME ZONE,
  status TEXT NOT NULL DEFAULT 'active',  -- active / expired / banned
  total_downloads INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 资源表
CREATE TABLE resources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,  -- r_a1b2c3d4 等加密名
  title TEXT NOT NULL,
  description TEXT,
  file_size INTEGER,
  min_plan TEXT NOT NULL DEFAULT 'free',  -- 最低可访问的会员等级
  download_count INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 下载记录表
CREATE TABLE downloads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  resource_id UUID REFERENCES resources(id),
  ip_address TEXT,
  user_agent TEXT,
  downloaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 联系留言表（备用，Formspree 仍可用）
CREATE TABLE contact_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT,
  email TEXT,
  message TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. 操作日志表（管理员行为追踪）
CREATE TABLE admin_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_email TEXT NOT NULL,
  action TEXT NOT NULL,  -- 'upgrade_user' / 'ban_user' / 'export_csv'
  target_user_id UUID,
  details JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_plan ON users(plan_id);
CREATE INDEX idx_downloads_user ON downloads(user_id);
CREATE INDEX idx_downloads_resource ON downloads(resource_id);

-- Row Level Security (RLS) 安全策略
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE resources ENABLE ROW LEVEL SECURITY;
ALTER TABLE downloads ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_logs ENABLE ROW LEVEL SECURITY;

-- 允许所有人读 resources（资源列表公开）
CREATE POLICY "Public read resources" ON resources
  FOR SELECT USING (true);

-- 用户只能更新自己的记录
CREATE POLICY "Users update own" ON users
  FOR UPDATE USING (auth.uid()::text = id::text);

-- 管理员可以读所有用户
CREATE POLICY "Admin read all users" ON users
  FOR SELECT USING (
    (SELECT email FROM users WHERE id = auth.uid()::text) = '2949465671@qq.com'
  );

-- 初始化 6 个资源
INSERT INTO resources (slug, title, description, file_size, min_plan) VALUES
  ('r_a1b2c3d4.docx', 'MaxKB FDE 教学讲义', '8 章节精讲 Word 讲义 · 46 KB', 47092, 'standard'),
  ('r_e5f6g7h8.pptx', 'MaxKB FDE 教学课件', '60 页紫色 AI 科技风 PPT · 495 KB', 506489, 'standard'),
  ('r_i9j0k1l2.py', 'MaxKB 核心模块源码', '8 大核心模块 Python 源码 · 500+ 行', 18814, 'standard'),
  ('r_m3n4o5p6.md', 'README', '完整使用说明 · 免费', 7000, 'free'),
  ('MaxKB_FDE教学资料_v1.0_小陶老师.zip', '总压缩包', '完整教学资料 · 1.8 MB', 1791715, 'standard'),
  ('images.zip', '教学配图包', '6 张高清配图 · 355 KB', 355379, 'standard');
```

---

## 🔑 第三步：获取 API 密钥（2 分钟）

### 在 Supabase Dashboard

1. 进入项目 → `Settings` → `API`
2. 复制两个值：
   - **Project URL**：`https://xxx.supabase.co`
   - **anon public key**：`eyJhbGc...`（长字符串）

### 在前端代码中

```javascript
const SUPABASE_URL = 'https://xxx.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGc...';
```

⚠️ **安全提示**：
- anon key 是公开的（前端必须可见）
- 不要把 service_role key 放到前端
- RLS 策略会保护数据安全

---

## 💻 第四步：前端代码改造（20-30 分钟）

### 4.1 引入 Supabase SDK

在 `index.html` `<head>` 末尾添加：

```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
```

### 4.2 创建 supabase-client.js

```javascript
// assets/js/supabase-client.js
const SUPABASE_URL = 'https://YOUR_PROJECT.supabase.co';
const SUPABASE_ANON_KEY = 'YOUR_ANON_KEY';

const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// 注册
async function registerUser(email, password) {
  const passwordHash = btoa(password);  // 简化版哈希（生产用 bcrypt）
  
  const { data, error } = await supabase
    .from('users')
    .insert([{ email, password_hash: passwordHash, plan_id: 'free' }])
    .select();
  
  if (error) {
    if (error.code === '23505') {
      return { success: false, error: '邮箱已注册' };
    }
    return { success: false, error: error.message };
  }
  
  return { success: true, user: data[0] };
}

// 登录
async function loginUser(email, password) {
  const passwordHash = btoa(password);
  
  const { data, error } = await supabase
    .from('users')
    .select('*')
    .eq('email', email)
    .eq('password_hash', passwordHash)
    .single();
  
  if (error || !data) {
    return { success: false, error: '邮箱或密码错误' };
  }
  
  return { success: true, user: data };
}

// 检查资源权限
async function checkResourceAccess(resourceSlug) {
  const user = getCurrentUser();
  const { data: resource } = await supabase
    .from('resources')
    .select('min_plan')
    .eq('slug', resourceSlug)
    .single();
  
  if (!resource) return false;
  
  const planLevel = { free: 0, standard: 1, flagship: 2 };
  return planLevel[user.plan_id] >= planLevel[resource.min_plan];
}

// 记录下载
async function trackDownload(resourceSlug) {
  const user = getCurrentUser();
  const { data: resource } = await supabase
    .from('resources')
    .select('id')
    .eq('slug', resourceSlug)
    .single();
  
  await supabase.from('downloads').insert([{
    user_id: user.id,
    resource_id: resource.id,
    ip_address: 'pending',  // 后端补
    user_agent: navigator.userAgent
  }]);
  
  // 更新下载计数
  await supabase.rpc('increment_download_count', {
    resource_id: resource.id,
    user_id: user.id
  });
}
```

### 4.3 替换原 localStorage 逻辑

在所有页面（`index.html`、`membership.html`、`user.html`、`admin.html`）中：
- 登录/注册 → 调用 `registerUser()` / `loginUser()`
- 下载资源 → 调用 `checkResourceAccess()` + `trackDownload()`
- 管理员后台 → 直接查询 Supabase 数据

---

## 👨‍💼 第五步：管理员后台升级（10 分钟）

### admin.html 显示真实用户

```javascript
// 从 Supabase 查询所有用户
async function loadUsers() {
  const { data: users } = await supabase
    .from('users')
    .select('*')
    .order('created_at', { ascending: false });
  
  renderUserList(users);
}

// 一键升级
async function upgradeUser(userId, newPlan) {
  await supabase
    .from('users')
    .update({ 
      plan_id: newPlan, 
      upgraded_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString()
    })
    .eq('id', userId);
  
  // 记录日志
  await supabase.from('admin_logs').insert([{
    admin_email: '2949465671@qq.com',
    action: 'upgrade_user',
    target_user_id: userId,
    details: { new_plan: newPlan }
  }]);
  
  loadUsers();  // 刷新列表
}

// CSV 导出
async function exportCSV() {
  const { data: users } = await supabase.from('users').select('*');
  
  let csv = 'email,plan,joined_at,downloads\n';
  users.forEach(u => {
    csv += `${u.email},${u.plan_id},${u.joined_at},${u.total_downloads}\n`;
  });
  
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `users_${new Date().toISOString().slice(0,10)}.csv`;
  a.click();
}
```

---

## 📈 第六步：数据看板（10 分钟）

### 管理员后台增加统计

```javascript
async function loadDashboard() {
  // 总用户数
  const { count: totalUsers } = await supabase
    .from('users')
    .select('*', { count: 'exact', head: true });
  
  // 各档会员数
  const { data: plans } = await supabase
    .from('users')
    .select('plan_id');
  
  const planCounts = { free: 0, standard: 0, flagship: 0 };
  plans.forEach(p => planCounts[p.plan_id]++);
  
  // 预估收入
  const revenue = planCounts.standard * 99 + planCounts.flagship * 299;
  
  // 总下载数
  const { count: totalDownloads } = await supabase
    .from('downloads')
    .select('*', { count: 'exact', head: true });
  
  // 渲染
  document.getElementById('stat-total').textContent = totalUsers;
  document.getElementById('stat-standard').textContent = planCounts.standard;
  document.getElementById('stat-flagship').textContent = planCounts.flagship;
  document.getElementById('stat-revenue').textContent = `¥${revenue}`;
  document.getElementById('stat-downloads').textContent = totalDownloads;
}
```

---

## 💰 第七步：升级成本与维护

### 成本
- Supabase 免费层：**永久 ¥0**
  - 500MB 数据库（约 5,000-50,000 用户）
  - 1GB 文件存储
  - 50K 月活用户
  - 2GB 出口流量

### 升级时机
- 用户 > 1,000 → 升级到 Pro ¥25/月
- 用户 > 10,000 → 升级到 Team ¥599/月

---

## 🔒 第八步：安全检查清单

| 项目 | 状态 |
|------|------|
| RLS 启用 | ✅ 必需 |
| anon key 仅前端 | ✅ 必需 |
| service_role key 永不上前端 | ✅ 必需 |
| 密码哈希（MVP 用 btoa，生产用 bcrypt） | ✅ MVP |
| HTTPS | ✅ GitHub Pages 自动 |

---

## ⏱️ 完整时间预估

| 步骤 | 时间 |
|------|------|
| 注册 Supabase | 3 分钟 |
| 创建项目 | 1 分钟 |
| 建表 SQL | 5 分钟 |
| 获取 API 密钥 | 2 分钟 |
| 前端代码改造 | 20-30 分钟 |
| 管理员后台升级 | 10 分钟 |
| 数据看板 | 10 分钟 |
| 测试 | 5 分钟 |
| **总计** | **45-60 分钟** |

---

## 🤖 小 Q 帮您做的事

1. ✅ 注册 Supabase（您授权 GitHub 登录）
2. ✅ 建表 SQL（粘贴执行即可）
3. ✅ 前端代码改造（替换 localStorage → Supabase SDK）
4. ✅ 管理员后台升级（显示真实用户）
5. ✅ 数据看板（真实数据统计）
6. ✅ 测试 + 部署

---

*生成时间：2026-07-23 22:40 · 由 AI 小 Q 为小陶老师定制*
*需要您授权「GitHub 登录」即可启动！*

📞 **遇到任何问题随时叫我** — Supabase 接入是小 Q 的强项领域！