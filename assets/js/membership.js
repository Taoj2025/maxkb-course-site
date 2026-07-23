// ============ 会员系统数据 ============
// 作者：小 Q 为小陶老师定制 · 2026-07-23

const MEMBERSHIP_PLANS = [
  {
    id: 'free',
    name: '体验会员',
    price: 0,
    period: '永久免费',
    color: '#94A3B8',
    icon: '🎓',
    description: '免费浏览课程大纲、章节简介、5 大企业场景',
    features: [
      { ok: true, text: '查看 8 章课程大纲' },
      { ok: true, text: '浏览 5 大企业场景' },
      { ok: true, text: '查看演示截图' },
      { ok: false, text: '完整课件下载' },
      { ok: false, text: '完整源码注释' },
      { ok: false, text: '实验指导手册' },
      { ok: false, text: '微信群 1V1 答疑' },
    ],
    cta: '免费注册',
    badge: '入门',
  },
  {
    id: 'standard',
    name: '标准会员',
    price: 99,
    period: '¥99/年',
    color: '#8B5CF6',
    icon: '⭐',
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
    cta: '立即升级',
    badge: '热门',
    highlight: true,
  },
  {
    id: 'flagship',
    name: '旗舰会员',
    price: 299,
    period: '¥299/年',
    color: '#5B2EBF',
    icon: '👑',
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
    cta: '成为旗舰',
    badge: '推荐',
  },
];

// 资源 -> 所需会员等级
// 0 = 体验 · 1 = 标准 · 2 = 旗舰
const RESOURCE_ACCESS = {
  'PPT': 1,                    // 标准会员
  'Word 讲义': 1,
  '源码': 1,
  'README': 1,
  'images.zip': 1,
  'MaxKB_FDE教学资料_v1.0.zip': 1,
};

// 会员状态管理（localStorage）
const MembershipStore = {
  getCurrent() {
    try {
      return JSON.parse(localStorage.getItem('maxkb_membership') || 'null');
    } catch (e) {
      return null;
    }
  },

  isLoggedIn() {
    return !!this.getCurrent();
  },

  getPlan() {
    const u = this.getCurrent();
    if (!u) return null;
    return MEMBERSHIP_PLANS.find(p => p.id === u.planId);
  },

  hasAccess(requiredPlanId) {
    const plan = this.getPlan();
    if (!plan) return false;
    const userLevel = ['free', 'standard', 'flagship'].indexOf(plan.id);
    const requiredLevel = ['free', 'standard', 'flagship'].indexOf(requiredPlanId);
    return userLevel >= requiredLevel;
  },

  login(email, password, planId = 'free') {
    const user = {
      email,
      password: btoa(password), // 简单编码，MVP 用
      planId,
      joinedAt: new Date().toISOString(),
    };
    localStorage.setItem('maxkb_membership', JSON.stringify(user));
    return user;
  },

  logout() {
    localStorage.removeItem('maxkb_membership');
  },

  upgrade(planId) {
    const u = this.getCurrent();
    if (u) {
      u.planId = planId;
      u.upgradedAt = new Date().toISOString();
      localStorage.setItem('maxkb_membership', JSON.stringify(u));
    }
  },
};