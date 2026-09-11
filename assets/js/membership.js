/**
 * MaxKB 会员系统 · v2 (2026-09-11)
 * 改动：完全去掉 localStorage 假数据，改用后端 API + JWT token
 * 兼容：保留 MEMBERSHIP_PLANS / MembershipStore.hasAccess 旧接口（其他页面可能引用）
 */

const MEMBERSHIP_PLANS = [
  {
    id: 'free', name: '体验会员', price: 0, period: '永久免费',
    color: '#94A3B8', icon: '🎓',
    description: '免费浏览课程大纲、章节简介、5 大企业场景',
    features: [
      { ok: true,  text: '查看 8 章课程大纲' },
      { ok: true,  text: '浏览 5 大企业场景' },
      { ok: true,  text: '查看演示截图' },
      { ok: false, text: '完整课件下载' },
      { ok: false, text: '完整源码注释' },
      { ok: false, text: '实验指导手册' },
      { ok: false, text: '微信群 1V1 答疑' },
    ],
    cta: '免费注册', badge: '入门',
  },
  {
    id: 'standard', name: '标准会员', price: 99, period: '¥99/年',
    color: '#8B5CF6', icon: '⭐',
    description: '完整课件 + 源码 + 实验手册，适合自学',
    features: [
      { ok: true, text: '体验会员所有权益' },
      { ok: true, text: '60 页 PPT 完整下载' },
      { ok: true, text: '8 章节讲义完整下载' },
      { ok: true, text: '8 大核心模块源码' },
      { ok: true, text: '3 个实验指导手册' },
      { ok: true, text: '5 大企业场景包' },
      { ok: false, text: '微信群 1V1 答疑' },
    ],
    cta: '立即升级', badge: '热门', highlight: true,
  },
  {
    id: 'flagship', name: '旗舰会员', price: 299, period: '¥299/年',
    color: '#5B2EBF', icon: '👑',
    description: '全部权益 + 1V1 答疑 + 项目实战辅导',
    features: [
      { ok: true, text: '标准会员所有权益' },
      { ok: true, text: '微信群 1V1 答疑' },
      { ok: true, text: '每月 1 次直播答疑' },
      { ok: true, text: '实战项目 1V1 辅导' },
      { ok: true, text: '专属会员证书' },
      { ok: true, text: '新课件优先获取' },
      { ok: true, text: '终身学习社群' },
    ],
    cta: '成为旗舰', badge: '推荐',
  },
];

const RESOURCE_ACCESS = {
  'PPT': 1, 'Word 讲义': 1, '源码': 1, 'README': 1,
  'images.zip': 1, 'MaxKB_FDE教学资料_v1.0.zip': 1,
};

// 会员状态管理 · 完全走后端
const MembershipStore = {
  /** 返回当前 user 或 null（来自缓存或 /me） */
  async getCurrent() {
    if (!window.MAXKB_API_TOKEN.get()) return null;
    let cached = window.MAXKB_API_USER.get();
    if (cached) return cached;
    try {
      const r = await window.api.me();
      window.MAXKB_API_USER.set(r.user);
      return r.user;
    } catch (e) {
      if (e.status === 401) return null;
      return null;
    }
  },

  isLoggedIn() { return !!window.MAXKB_API_TOKEN.get(); },

  getPlan() {
    const u = window.MAXKB_API_USER.get();
    if (!u) return null;
    return MEMBERSHIP_PLANS.find(p => p.id === u.plan_id) || null;
  },

  /** 检查当前 user 对 requiredPlanId 是否有访问权限 */
  hasAccess(requiredPlanId) {
    const plan = this.getPlan();
    if (!plan) return false;
    const lv = { free: 0, standard: 1, flagship: 2 };
    return (lv[plan.id] ?? 0) >= (lv[requiredPlanId] ?? 0);
  },

  async login(email, password) {
    const r = await window.api.login(email, password);
    window.MAXKB_API_TOKEN.set(r.token);
    window.MAXKB_API_USER.set(r.user);
    document.dispatchEvent(new CustomEvent('maxkb:auth:login', { detail: r.user }));
    return r.user;
  },

  async register(email, password) {
    const r = await window.api.register(email, password);
    window.MAXKB_API_TOKEN.set(r.token);
    window.MAXKB_API_USER.set(r.user);
    document.dispatchEvent(new CustomEvent('maxkb:auth:login', { detail: r.user }));
    return r.user;
  },

  logout() { window.api.logout(); },

  async upgrade(planId) {
    // 用户无法自助升级（需要管理员）—— 仅做 UI 提示
    throw new Error('请通过 membership.html 申请升级，由小陶老师人工开通');
  },
};

// 暴露给其他页面用
window.MEMBERSHIP_PLANS = MEMBERSHIP_PLANS;
window.MembershipStore = MembershipStore;
