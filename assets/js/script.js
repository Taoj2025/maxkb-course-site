/**
 * MaxKB FDE 教学网站 · 交互脚本 v2 (2026-09-11)
 * 改动：
 *   - 课程章节从 /api/chapters 渲染（失败 fallback assets/js/data.js 的 chapters 数组）
 *   - 资讯从 /api/articles 渲染（失败 fallback articles.json）
 *   - 顶部状态条基于真实 token + /me
 *   - 资源下载鉴权改为调 /api/download/:slug（带 JWT）
 *   - 联系表单优先 POST /api/contact，失败 fallback Formspree
 */

(function () {
  // ============ 顶部会员状态条 ============
  async function refreshTopStatusBar() {
    const bar = document.getElementById('top-status-bar');
    if (!bar) return;

    if (!window.MAXKB_API_TOKEN.get()) {
      bar.style.background = 'rgba(0,0,0,0.25)';
      bar.innerHTML = '<span id="status-text">💎 未登录 · 访问全部资源需会员</span>'
        + '<a href="membership.html" style="color: #FCD34D; text-decoration: none; margin-left: 12px; font-weight: 600;">👤 登录 / 注册</a>';
      return;
    }

    let user = window.MAXKB_API_USER.get();
    if (!user) {
      try {
        const r = await window.api.me();
        user = r.user;
        window.MAXKB_API_USER.set(user);
      } catch (e) {
        window.api.logout();
        return refreshTopStatusBar();
      }
    }

    const plan = (window.MEMBERSHIP_PLANS || []).find(p => p.id === user.plan_id);
    if (!plan) return;

    let remainingDays = 0;
    if (user.expires_at) {
      remainingDays = Math.max(0, Math.ceil((new Date(user.expires_at) - Date.now()) / 86400000));
    } else if (plan.id !== 'free') {
      remainingDays = 365;  // 默认 1 年（admin 升级时设置）
    }

    bar.style.background =
      plan.id === 'flagship' ? 'linear-gradient(90deg, #5B2EBF, #8B5CF6)' :
      plan.id === 'standard' ? 'linear-gradient(90deg, #3B82F6, #60A5FA)' :
      'rgba(0,0,0,0.3)';

    bar.innerHTML = `
      <span style="font-weight:600;">${plan.icon} 您是【${plan.name}】 · ${user.email}${plan.id !== 'free' ? ' · 剩余 ' + remainingDays + ' 天' : ''}</span>
      <a href="user.html" style="color: #FCD34D; text-decoration: none; margin-left: 12px; font-weight: 600;">${plan.id === 'free' ? '⚡ 升级会员' : '⚙️ 个人中心'}</a>
      <a href="#" id="top-logout" style="color: rgba(255,255,255,0.7); text-decoration: none; margin-left: 12px; font-size: 12px;">退出</a>
    `;
    const logoutBtn = document.getElementById('top-logout');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (confirm('确认退出？')) { window.api.logout(); location.reload(); }
      });
    }
  }

  function updateDownloadHint() {
    const hint = document.getElementById('download-hint');
    if (!hint) return;
    const user = window.MAXKB_API_USER.get();
    const planId = user && user.plan_id;

    if (!user) {
      hint.textContent = '（提示：5/6 资源需会员，README 免费可下）';
      hint.style.color = 'var(--gray)';
    } else if (planId === 'flagship' || planId === 'standard') {
      hint.textContent = '（您是' + (planId === 'flagship' ? '旗舰' : '标准') + '会员，全部资源已解锁 ✓）';
      hint.style.color = '#34D399';
    } else {
      hint.textContent = '（您是体验会员，仅 README 可下载）';
      hint.style.color = 'var(--gray)';
    }
  }

  // ============ 渲染课程章节（API + fallback）============
  async function renderChapters(filter = 'all') {
    const grid = document.getElementById('chapter-grid');
    if (!grid) return;

    let data;
    try {
      const res = await window.api.chapters();
      data = (res.items || []).map(c => ({
        id: c.id, title: c.title, desc: c.description, icon: c.icon,
        tag: c.tag, duration: c.duration, pages: c.pages, outputs: c.outputs || [],
      }));
    } catch (e) {
      // fallback 到内置 chapters 数组（assets/js/data.js）
      data = (window.chapters || []).map(c => ({
        id: c.id, title: c.title, desc: c.desc, icon: c.icon,
        tag: c.tag, duration: c.duration, pages: c.pages, outputs: c.outputs || [],
      }));
    }

    const filtered = filter === 'all' ? data : data.filter(c => c.tag === filter);
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
          ${(ch.outputs || []).map(o => `<span style="display:inline-block; background:var(--gray-light); padding:3px 10px; border-radius:6px; font-size:11px; color:var(--gray); margin-right:6px; margin-bottom:4px;">✓ ${o}</span>`).join('')}
        </div>
        <div class="actions">
          <a href="#course">查看详情</a>
          <a href="downloads/MaxKB_FDE教学课件_小陶老师.pptx" class="primary">下载 PPT</a>
        </div>
      </div>
    `).join('');
  }

  // ============ 渲染资讯（API + fallback）============
  async function renderArticles(size = 8) {
    const grid = document.getElementById('news-grid');
    if (!grid) return;

    let items;
    try {
      const r = await window.api.articles({ size });
      items = r.items;
    } catch (e) {
      try {
        items = await fetch('articles.json').then(r => r.json());
        items = items.slice(0, size);
      } catch { items = []; }
    }

    if (!items.length) {
      grid.innerHTML = '<p style="color:var(--gray); text-align:center; padding: 40px;">暂无文章</p>';
      return;
    }

    const colorMap = { 'purple': '#8B5CF6', 'blue': '#3B82F6', 'orange': '#F59E0B', 'success-green': '#34D399', 'warning-yellow': '#FCD34D' };
    grid.innerHTML = items.map(a => {
      const tag = a.tags && a.tags[0] ? a.tags[0] : (a.category || '');
      const color = colorMap[a.color] || '#8B5CF6';
      return `
        <div class="news-card">
          <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
            <span style="background:${color}; color:white; padding:4px 10px; border-radius:6px; font-size:12px;">${escapeHtml(tag)}</span>
            <span style="color:var(--gray); font-size:12px;">${(a.published_at || '').slice(0, 10)}</span>
          </div>
          <h3 style="font-size:18px; margin-bottom:12px; color:var(--purple-deep);">${escapeHtml(a.title)}</h3>
          <p style="color:var(--gray); font-size:14px; line-height:1.6; margin-bottom:16px;">${escapeHtml((a.summary || '').slice(0, 80))}</p>
          <a href="article.html?slug=${encodeURIComponent(a.slug)}" style="color: var(--purple); font-weight: 600; font-size: 14px;">阅读全文 →</a>
        </div>
      `;
    }).join('');
  }

  function escapeHtml(s) {
    return String(s || '').replace(/[&<>"']/g, c => ({ '&': '&', '<': '<', '>': '>', '"': '"', "'": '&#39;' }[c]));
  }

  // ============ 章节标签切换 ============
  function initChapterTabs() {
    document.querySelectorAll('.chapter-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.chapter-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        renderChapters(tab.dataset.tab);
      });
    });
  }

  // ============ 导航高亮 ============
  function initNavHighlight() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');
    if (!sections.length || !navLinks.length) return;
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

  // ============ 联系表单（API 优先 + Formspree fallback）============
  function initContactForm() {
    const form = document.getElementById('contact-form');
    if (!form) return;
    const status = document.getElementById('form-status');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (status) { status.style.color = 'rgba(255,255,255,0.7)'; status.textContent = '⏳ 正在提交...'; }
      const data = Object.fromEntries(new FormData(form));

      try {
        await window.api.contact({ ...data, source: 'index' });
        if (status) { status.style.color = '#34D399'; status.textContent = '✅ 提交成功！小陶老师会尽快联系您（24 小时内）。'; }
        form.reset();
      } catch (err) {
        // fallback Formspree（保持原有提交方式）
        try {
          const res = await fetch(form.action, {
            method: 'POST', body: new FormData(form),
            headers: { 'Accept': 'application/json' }
          });
          if (res.ok) {
            if (status) { status.style.color = '#34D399'; status.textContent = '✅ 提交成功！小陶老师会尽快联系您。'; }
            form.reset();
          } else { throw new Error('Formspree fail'); }
        } catch (err2) {
          if (status) { status.style.color = '#FCA5A5'; status.textContent = '❌ 提交失败，请直接微信联系小陶老师。'; }
        }
      }
    });
  }

  // ============ 平滑滚动 ============
  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(link => {
      link.addEventListener('click', (e) => {
        const target = document.querySelector(link.getAttribute('href'));
        if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
      });
    });
  }

  // ============ 资源下载鉴权（事件委托）============
  async function initResourceGating() {
    refreshTopStatusBar();
    updateDownloadHint();

    // 监听登录/登出事件，刷新状态条
    document.addEventListener('maxkb:auth:login',  refreshTopStatusBar);
    document.addEventListener('maxkb:auth:logout', () => { window.MAXKB_API_USER.set(null); refreshTopStatusBar(); updateDownloadHint(); });

    document.addEventListener('click', async (e) => {
      const link = e.target.closest('a[data-need-membership="true"]');
      if (!link) return;

      const resource = link.closest('.resource');
      const minPlan  = resource?.dataset.minPlan || 'standard';
      const slug     = link.getAttribute('href')?.split('/').pop();

      // 未登录
      if (!window.MAXKB_API_TOKEN.get()) {
        e.preventDefault(); e.stopPropagation();
        if (confirm(`🔒 此资源需要「${planName(minPlan)}」会员才能下载。\n\n您当前未登录。\n\n点击「确定」前往注册页面。`)) {
          sessionStorage.setItem('pending_download', slug);
          window.location.href = 'membership.html';
        }
        return;
      }

      // 已登录 → 调后端鉴权下载
      e.preventDefault(); e.stopPropagation();
      const result = await window.api.download(slug);
      if (result.ok) {
        console.log('[下载成功]', slug);
      } else if (result.reason === 'upgrade_needed') {
        if (confirm(`🔒 此资源需要「${planName(result.requiredPlan)}」会员才能下载。\n\n点击「确定」前往升级页面。`)) {
          window.location.href = 'membership.html';
        }
      } else if (result.reason === 'token_expired') {
        alert('登录已过期，请重新登录');
        window.location.href = 'membership.html';
      } else if (result.reason === 'not_logged_in') {
        if (confirm('请先登录。\n\n点击「确定」前往登录页面。')) {
          window.location.href = 'membership.html';
        }
      } else {
        alert('下载失败：' + result.reason + '\n请稍后重试或联系管理员。');
      }
    });
  }

  function planName(planId) {
    return ({ 'free': '体验', 'standard': '标准（¥99/年）', 'flagship': '旗舰（¥299/年）' })[planId] || planId;
  }

  // ============ 初始化 ============
  document.addEventListener('DOMContentLoaded', async () => {
    initChapterTabs();
    initNavHighlight();
    initContactForm();
    initSmoothScroll();
    initFaqAccordion();
    initHamburger();
    await initResourceGating();
    await renderArticles(8);
  });

  // ============ FAQ Accordion 切换 ============
  function initFaqAccordion() {
    document.querySelectorAll('.faq-accordion .faq-q').forEach(btn => {
      btn.addEventListener('click', () => {
        const item = btn.closest('.faq-item');
        const wasOpen = item.classList.contains('open');
        // 关闭其他
        document.querySelectorAll('.faq-accordion .faq-item.open').forEach(el => el.classList.remove('open'));
        // 切换当前
        if (!wasOpen) item.classList.add('open');
      });
    });
  }

  // ============ Hamburger 切换 ============
  function initHamburger() {
    const btn = document.getElementById('nav-hamburger');
    const links = document.getElementById('nav-links');
    if (!btn || !links) return;
    btn.addEventListener('click', () => {
      links.classList.toggle('open');
      btn.textContent = links.classList.contains('open') ? '✕' : '☰';
    });
    links.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
      links.classList.remove('open');
      btn.textContent = '☰';
    }));
  }

  // 暴露给外部
  window.MAXKB_UI = {
    renderChapters,
    renderArticles,
    refreshTopStatusBar,
    updateDownloadHint,
  };
})();
