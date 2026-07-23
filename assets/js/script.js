// ============ MaxKB FDE 教学网站 · 交互脚本 ============
// 作者：小 Q 为小陶老师定制 · 2026-07-23

// ============ 0. 顶部会员状态条 ============
function updateTopStatusBar() {
  const bar = document.getElementById('top-status-bar');
  const text = document.getElementById('status-text');
  if (!bar) return;

  const plan = MembershipStore.getPlan();
  const user = MembershipStore.getCurrent();

  if (!user || !plan) {
    bar.style.background = 'rgba(0,0,0,0.25)';
    bar.innerHTML = '<span id="status-text">💎 未登录 · 访问全部资源需会员</span><a href="membership.html" style="color: #FCD34D; text-decoration: none; margin-left: 12px; font-weight: 600;">👤 登录 / 注册</a>';
  } else {
    const joinedDate = new Date(user.joinedAt);
    const expiresDate = new Date(joinedDate);
    expiresDate.setFullYear(expiresDate.getFullYear() + 1);
    const remainingDays = Math.max(0, Math.ceil((expiresDate - new Date()) / (1000 * 60 * 60 * 24)));
    bar.style.background = plan.id === 'flagship' ? 'linear-gradient(90deg, #5B2EBF, #8B5CF6)' :
                            plan.id === 'standard' ? 'linear-gradient(90deg, #3B82F6, #60A5FA)' :
                            'rgba(0,0,0,0.3)';
    bar.innerHTML = `
      <span style="font-weight:600;">${plan.icon} 您是【${plan.name}】 · ${user.email} · 剩余 ${remainingDays} 天</span>
      <a href="membership.html" style="color: #FCD34D; text-decoration: none; margin-left: 12px; font-weight: 600;">${plan.id === 'free' ? '⚡ 升级会员' : '⚙️ 管理会员'}</a>
      <a href="#" id="top-logout" style="color: rgba(255,255,255,0.7); text-decoration: none; margin-left: 12px; font-size: 12px;">退出</a>
    `;
    const logoutBtn = document.getElementById('top-logout');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (confirm('确认退出？')) {
          MembershipStore.logout();
          location.reload();
        }
      });
    }
  }
}

// ============ 1. 渲染课程章节 ============
function renderChapters(filter = 'all') {
  const grid = document.getElementById('chapter-grid');
  if (!grid) return;
  const filtered = filter === 'all' ? chapters : chapters.filter(c => c.tag === filter);
  grid.innerHTML = filtered.map(ch => `
    <div class="chapter-card" data-tag="${ch.tag}">
      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
        <div style="font-size: 28px;">${ch.icon}</div>
        <div style="flex: 1;">
          <div style="font-size: 12px; color: var(--gray); margin-bottom: 4px;">
            第 ${ch.id} 章 · ${ch.duration} · ${ch.pages}
          </div>
        </div>
      </div>
      <h3>${ch.title}</h3>
      <p>${ch.desc}</p>
      <div class="meta">
        <span>⏱️ ${ch.duration}</span>
        <span>📄 ${ch.pages}</span>
      </div>
      <div style="margin-bottom: 16px;">
        ${ch.outputs.map(o => `<span style="display:inline-block; background:var(--gray-light); padding:3px 10px; border-radius:6px; font-size:11px; color:var(--gray); margin-right:6px; margin-bottom:4px;">✓ ${o}</span>`).join('')}
      </div>
      <div class="actions">
        <a href="#course">查看详情</a>
        <a href="downloads/MaxKB_FDE教学课件_小陶老师.pptx" class="primary">下载 PPT</a>
      </div>
    </div>
  `).join('');
}

// ============ 2. 章节标签切换 ============
function initChapterTabs() {
  const tabs = document.querySelectorAll('.chapter-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      renderChapters(tab.dataset.tab);
    });
  });
}

// ============ 3. 导航高亮 ============
function initNavHighlight() {
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');
  window.addEventListener('scroll', () => {
    let current = '';
    sections.forEach(section => {
      const sectionTop = section.offsetTop - 100;
      if (window.scrollY >= sectionTop) current = section.id;
    });
    navLinks.forEach(link => {
      link.classList.remove('active');
      if (link.getAttribute('href') === '#' + current) link.classList.add('active');
    });
  });
}

// ============ 4. 表单提交（Formspree AJAX）============
function initContactForm() {
  const form = document.getElementById('contact-form');
  if (!form) return;
  const status = document.getElementById('form-status');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (status) {
      status.style.color = 'rgba(255,255,255,0.7)';
      status.textContent = '⏳ 正在提交...';
    }
    const data = new FormData(form);
    try {
      const res = await fetch(form.action, {
        method: 'POST',
        body: data,
        headers: { 'Accept': 'application/json' }
      });
      if (res.ok) {
        if (status) {
          status.style.color = '#34D399';
          status.textContent = '✅ 提交成功！小陶老师会通过微信/邮箱主动联系您（24 小时内）。';
        }
        form.reset();
      } else {
        throw new Error('提交失败');
      }
    } catch (err) {
      if (status) {
        status.style.color = '#FCA5A5';
        status.textContent = '❌ 提交失败，请稍后重试或直接微信联系小陶老师。';
      }
    }
  });
}

// ============ 5. 平滑滚动 ============
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', (e) => {
      const target = document.querySelector(link.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

// ============ 6. 资源权限拦截（事件委托版 · 极稳健）============
function initResourceGating() {
  console.log('[会员拦截] 初始化中...');
  console.log('[会员拦截] 当前 MembershipStore:', typeof MembershipStore !== 'undefined' ? '已加载' : '未加载');

  updateTopStatusBar();
  updateDownloadHint();

  // ⭐ 关键修改：使用事件委托，监听整个文档，避免动态加载的链接丢失
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a[data-need-membership="true"]');
    if (!link) return;

    console.log('[会员拦截] 检测到点击:', link.getAttribute('href'));

    const resource = link.closest('.resource');
    const minPlan = resource?.dataset.minPlan || 'standard';

    if (MembershipStore.hasAccess(minPlan)) {
      console.log('[会员拦截] ✅ 权限通过，开始下载');
      trackDownload(link.getAttribute('href'));
      return; // 放行
    }

    // ⭐ 必须阻止默认行为 + 阻止冒泡（防止外层跳转）
    e.preventDefault();
    e.stopPropagation();

    const isLoggedIn = MembershipStore.isLoggedIn();
    const currentPlan = MembershipStore.getPlan();

    if (!isLoggedIn) {
      console.log('[会员拦截] ❌ 未登录，引导注册');
      if (confirm(`🔒 此资源需要「${planName(minPlan)}」会员才能下载。\n\n您当前未登录。\n\n点击「确定」前往注册页面。`)) {
        sessionStorage.setItem('pending_download', link.getAttribute('href'));
        window.location.href = 'membership.html';
      }
    } else if (currentPlan) {
      console.log('[会员拦截] ❌ 权限不足，引导升级');
      if (confirm(`🔒 此资源需要「${planName(minPlan)}」会员才能下载。\n\n您当前是「${currentPlan.name}」。\n\n点击「确定」前往升级页面。`)) {
        window.location.href = 'membership.html';
      }
    }
  });
}

// ============ 7. 顶部下载提示 ============
function updateDownloadHint() {
  const hint = document.getElementById('download-hint');
  if (!hint) return;
  const user = MembershipStore.getCurrent();
  const plan = MembershipStore.getPlan();

  if (!user) {
    hint.textContent = '（提示：5/6 资源需会员，README 免费可下）';
    hint.style.color = 'var(--gray)';
  } else if (plan) {
    if (plan.id === 'flagship') {
      hint.textContent = '（您是旗舰会员，全部资源已解锁 ✓）';
      hint.style.color = '#34D399';
    } else if (plan.id === 'standard') {
      hint.textContent = '（您是标准会员，全部资源已解锁 ✓）';
      hint.style.color = '#34D399';
    } else {
      hint.textContent = '（您是体验会员，仅 README 可下载）';
      hint.style.color = 'var(--gray)';
    }
  }
}

// ============ 8. 跟踪下载次数（个人中心用）============
function trackDownload(url) {
  const count = parseInt(localStorage.getItem('maxkb_downloads') || '0');
  localStorage.setItem('maxkb_downloads', count + 1);
  console.log('[下载追踪]', url, '总数:', count + 1);
}

function planName(planId) {
  return { 'free': '体验', 'standard': '标准（¥99/年）', 'flagship': '旗舰（¥299/年）' }[planId] || planId;
}

// ============ 初始化 ============
document.addEventListener('DOMContentLoaded', () => {
  console.log('[初始化] DOMContentLoaded');
  renderChapters();
  initChapterTabs();
  initNavHighlight();
  initContactForm();
  initSmoothScroll();
  initResourceGating();  // ⭐ 修改名称为 initResourceGating
  console.log('[初始化] 完成');
});