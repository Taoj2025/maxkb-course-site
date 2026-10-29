"""给缺汉堡按钮的页面补上（≤1279px 收成汉堡菜单）。

用法：python scripts/add-hamburger.py
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BTN = '    <button class="hamburger" id="nav-hamburger" aria-label="菜单">☰</button>\n'

SCRIPT = '''
<script>
// 汉堡菜单（≤1279px 时导航收起）
(function () {
  var btn = document.getElementById('nav-hamburger');
  var links = document.getElementById('nav-links');
  if (!btn || !links) return;
  btn.addEventListener('click', function () {
    links.classList.toggle('open');
    btn.textContent = links.classList.contains('open') ? '✕' : '☰';
  });
  links.querySelectorAll('a').forEach(function (a) {
    a.addEventListener('click', function () {
      links.classList.remove('open');
      btn.textContent = '☰';
    });
  });
})();
</script>
'''

PAGES = ["faq.html", "latest.html", "fde-jobs.html", "fde-skills.html"]

for page in PAGES:
    p = os.path.join(ROOT, page)
    s = io.open(p, encoding="utf-8").read()
    if "nav-hamburger" in s:
        print("skip %s" % page)
        continue
    # 按钮插到 <div class="nav-links"> 之前
    anchor = '    <div class="nav-links"'
    if anchor not in s:
        anchor = '  <div class="nav-links"'
    i = s.find(anchor)
    if i < 0:
        print("!! %s 找不到 .nav-links" % page)
        continue
    s = s[:i] + BTN + s[i:]
    # 脚本插到 </body> 之前
    j = s.rfind("</body>")
    if j < 0:
        print("!! %s 找不到 </body>" % page)
        continue
    s = s[:j] + SCRIPT + s[j:]
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("ok  %s" % page)
