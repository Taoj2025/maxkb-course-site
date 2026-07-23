// ============ MaxKB FDE 教学网站 · 交互脚本 ============
// 作者：小 Q 为小陶老师定制 · 2026-07-23

// ============ 0. 邀请码验证（受邀测试模式）============
const INVITE_CODE = 'maxkb2026';
function initInviteGate() {
  const gate = document.getElementById('invite-gate');
  const form = document.getElementById('invite-form');
  const input = document.getElementById('invite-code-input');
  const submit = document.getElementById('invite-submit');
  const status = document.getElementById('invite-status');
  if (!gate || !form) return;

  // 已解锁过？直接跳过闸门
  const unlocked = localStorage.getItem('maxkb_invite') === '1';
  if (unlocked) {
    gate.style.display = 'none';
    form.style.display = 'block';
    return;
  }

  submit.addEventListener('click', () => {
    const code = (input.value || '').trim().toLowerCase();
    if (code === INVITE_CODE) {
      status.style.color = '#34D399';
      status.textContent = '✅ 邀请码正确！解锁中...';
      localStorage.setItem('maxkb_invite', '1');
      setTimeout(() => {
        gate.style.display = 'none';
        form.style.display = 'block';
      }, 600);
    } else {
      status.style.color = '#FCA5A5';
      status.textContent = '❌ 邀请码不正确，请联系小陶老师获取。';
    }
  });

  // 按 Enter 也能验证
  input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      submit.click();
    }
  });
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

// ============ 初始化 ============
document.addEventListener('DOMContentLoaded', () => {
  initInviteGate();
  renderChapters();
  initChapterTabs();
  initNavHighlight();
  initContactForm();
  initSmoothScroll();
  console.log('✅ MaxKB FDE 教学网站已就绪 · 2026-07-23');
});