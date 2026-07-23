// ============ MaxKB FDE 教学网站 · 交互脚本 ============
// 作者：小 Q 为小陶老师定制 · 2026-07-23

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

// ============ 5.5 会员资源权限拦截 ============
function initMembershipGating() {
  const hint = document.getElementById('download-hint');
  const links = document.querySelectorAll('a[data-need-membership="true"]');

  const plan = MembershipStore.getPlan();
  const isLoggedIn = MembershipStore.isLoggedIn();

  // 顶部提示
  if (hint) {
    if (!isLoggedIn) {
      hint.textContent = '（会员资源 ·  会员中心注册后可解锁）';
    } else if (plan) {
      hint.textContent = `（当前为「${plan.name}」· ${plan.id === 'free' ? '升级到标准会员可下载完整资料' : '感谢支持！'}）`;
    }
  }

  // 拦截下载点击
  links.forEach(link => {
    link.addEventListener('click', (e) => {
      const resource = link.closest('.resource');
      const minPlan = resource?.dataset.minPlan || 'standard';
      if (!MembershipStore.hasAccess(minPlan)) {
        e.preventDefault();
        if (!isLoggedIn) {
          if (confirm('🔒 此资源需会员下载。\n\n是否立即注册体验会员？')) {
            window.location.href = 'membership.html';
          }
        } else {
          if (confirm('🔒 此资源需标准会员及以上。\n\n是否立即升级？')) {
            window.location.href = 'membership.html';
          }
        }
      }
    });
  });
}

// ============ 初始化 ============
document.addEventListener('DOMContentLoaded', () => {
  renderChapters();
  initChapterTabs();
  initNavHighlight();
  initContactForm();
  initSmoothScroll();
  initMembershipGating();
  console.log('✅ MaxKB FDE 教学网站已就绪 · 2026-07-23');
});