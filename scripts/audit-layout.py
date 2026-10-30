#!/usr/bin/env python3
"""全站布局体检：横向溢出 / 图片加载失败 / JS 报错 / 关键组件是否在位。

用法：python scripts/audit-layout.py [--shots]
     --shots 额外给首页和移动端截图，输出到 .audit/
"""

import os
import subprocess
import sys
import threading
import http.server
import socketserver
import functools

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
PORT = 8765

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shell  # noqa: E402

# admin.html 是独立的后台控制台，不属于公开站点，不参与这套体检
PAGES = [p for p in sorted(os.listdir(SITE))
         if p.endswith(".html") and p not in shell.SKIP]


def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=SITE)
    handler.log_message = lambda *a, **k: None
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def main():
    shots = "--shots" in sys.argv
    from playwright.sync_api import sync_playwright

    httpd = serve()
    outdir = os.path.join(ROOT, ".audit")
    if shots:
        os.makedirs(outdir, exist_ok=True)

    bad_total = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for page_name in PAGES:
                errors = []
                broken = []
                missing = []
                ctx = browser.new_context(viewport={"width": 1440, "height": 900})
                pg = ctx.new_page()
                pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
                pg.on("pageerror", lambda e: errors.append(str(e)))
                pg.on("response", lambda r: missing.append("%s %s" % (r.status, r.url))
                      if r.status >= 400 else None)
                pg.goto("http://127.0.0.1:%d/%s" % (PORT, page_name), wait_until="networkidle")
                pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                pg.wait_for_timeout(600)
                pg.evaluate("window.scrollTo(0, 0)")
                pg.wait_for_timeout(200)

                info = pg.evaluate("""() => {
                  const d = document.documentElement;
                  const imgs = [...document.images];
                  const nav = document.getElementById('site-nav');
                  const drop = document.querySelector('.nav-drop');
                  // 重复 id 是无效 HTML —— getElementById 只认第一个，
                  // 多出来的控件就永远点不到。2026-10-30 就在吸底 CTA 上踩过。
                  const seen = {}, dupIds = [];
                  document.querySelectorAll('[id]').forEach(el => {
                    if (seen[el.id]) dupIds.push(el.id); else seen[el.id] = true;
                  });
                  // 合法属性名长这样：class / id / data-x / aria-x / xlink:href
                  const OK_NAME = /^[A-Za-z_:][A-Za-z0-9_:.\-]*$/;
                  return {
                    overflow: d.scrollWidth - d.clientWidth,
                    // 只算「有 src 但加载不出来」的才算裂图；
                    // 灯箱里那个占位 <img alt=""> 本来就没有 src，不算
                    broken: imgs.filter(i => i.getAttribute('src') && i.complete && i.naturalWidth === 0).map(i => i.src),
                    imgs: imgs.length,
                    navH: nav ? Math.round(nav.getBoundingClientRect().height) : -1,
                    navTop: nav ? Math.round(nav.getBoundingClientRect().top) : -1,
                    dropW: drop ? Math.round(drop.getBoundingClientRect().width) : -1,
                    hasMcta: !!document.querySelector('.mcta'),
                    hasCrumb: !!document.querySelector('.crumb'),
                    hasFooter: !!document.querySelector('footer.footer'),
                    bodyPadTop: getComputedStyle(document.body).paddingTop,
                    dupIds: dupIds,
                    // 属性被写坏：class="class="sec-wrap"" 这种嵌套写法，
                    // 或者 onerror 里再套一层 style="..." 把属性值提前截断。
                    // 两种坏法的共同特征是「属性名本身不合法」——
                    // 浏览器会把多出来的部分当成另一个属性名，名字里带引号/分号/冒号。
                    // 只看属性名不看属性值：值里出现 " 是合法的（&quot; 转义），
                    // 图标那条 data:image/svg+xml 的值里还带 < 呢。
                    badAttrs: [...document.querySelectorAll('*')]
                      .filter(el => [...el.attributes].some(
                        a => !OK_NAME.test(a.name)))
                      .slice(0, 3)
                      .map(el => el.tagName + '.' + (el.className || '').toString().slice(0, 24)),
                    // .sec-wrap 必须真的被限到 1280px —— 规则写错成 .sec > .sec-wrap
                    // 就会静默失效，内容直接顶到屏幕两边，体检也看不出来
                    wrapBad: [...document.querySelectorAll('.sec-wrap')]
                      .filter(el => el.getBoundingClientRect().width > 1281)
                      .slice(0, 3)
                      .map(el => 'w=' + Math.round(el.getBoundingClientRect().width)),
                    // 外壳区域必须各只有一份（脚本重复执行会积出好几份）
                    counts: {
                      nav: document.querySelectorAll('nav.navbar').length,
                      crumb: document.querySelectorAll('nav.crumb').length,
                      footer: document.querySelectorAll('footer.footer').length,
                      status: document.querySelectorAll('#top-status-bar').length,
                      mcta: document.querySelectorAll('.mcta').length,
                      totop: document.querySelectorAll('.to-top').length,
                    },
                  };
                }""")
                # 横向溢出元素定位
                wide = pg.evaluate("""() => {
                  const vw = document.documentElement.clientWidth;
                  const out = [];
                  document.querySelectorAll('body *').forEach(el => {
                    const r = el.getBoundingClientRect();
                    if (r.width > 0 && (r.right > vw + 2 || r.left < -2)) {
                      out.push((el.tagName + '.' + (el.className || '').toString().split(' ')[0]).slice(0, 46)
                               + ' right=' + Math.round(r.right));
                    }
                  });
                  return out.slice(0, 5);
                }""")

                issues = []
                # 本地静态服务器没有后端和动态数据，
                # articles.json / data/*.json / api/* 线上是转发到源站的，
                # 在这里 404 是预期的，不算问题。
                PROXIED = ("/api/", "articles.json", "data/", "fde-jobs.json")
                real_missing = [m for m in missing
                                if not any(k in m.split(" ", 1)[1] for k in PROXIED)]
                real_errors = [e for e in errors
                               if "Failed to load resource" not in e
                               and "ERR_FAILED" not in e
                               and "blocked by CORS" not in e
                               and "is not valid JSON" not in e
                               # /data/* 线上是转发到源站的（vercel.json 的 rewrites），
                               # 本地静态服务器里没有这个目录 → 404 是预期的。
                               # fde-jobs.html 会把它报成 "加载 fde-jobs.json 失败"，
                               # 那也是预期内的，别当成真错。
                               and "fde-jobs.json" not in e]
                if info["overflow"] > 2:
                    issues.append("横向溢出 %dpx" % info["overflow"])
                if info["broken"]:
                    issues.append("图片裂图 %d" % len(info["broken"]))
                if real_errors:
                    issues.append("JS 报错 %d" % len(real_errors))
                if real_missing:
                    issues.append("资源 404 %d" % len(real_missing))
                if info["navH"] < 40:
                    issues.append("导航没渲染")
                if info["dupIds"]:
                    issues.append("重复 id %d 个(%s)"
                                  % (len(info["dupIds"]), ",".join(info["dupIds"][:3])))
                if info["badAttrs"]:
                    issues.append("坏属性 %s" % ",".join(info["badAttrs"]))
                if info["wrapBad"]:
                    issues.append("内层容器没限宽 %s" % ",".join(info["wrapBad"]))
                # 首页本来就没有面包屑，其余页面必须有且只有一份
                want = {"nav": 1, "crumb": 0 if page_name == "index.html" else 1,
                        "footer": 1, "status": 1, "mcta": 1, "totop": 1}
                for k, w in want.items():
                    got = info["counts"].get(k, 0)
                    if got != w:
                        issues.append("%s 应 %d 份实际 %d 份" % (k, w, got))

                status = "✅" if not issues else "❌"
                if issues:
                    bad_total += 1
                print("%s %-24s 导航 %3dpx · 溢出 %3d · 图 %2d/%2d · %s"
                      % (status, page_name, info["navH"], info["overflow"],
                         info["imgs"] - len(info["broken"]), info["imgs"],
                         "; ".join(issues)))
                for b in info["broken"][:4]:
                    print("      裂图:", b.split("/")[-1])
                for m in real_missing[:5]:
                    print("      404:", m.replace("http://127.0.0.1:%d/" % PORT, ""))
                for e in real_errors[:3]:
                    print("      JS:", e[:140])
                for w in wide[:3]:
                    print("      溢出:", w)

                if shots and page_name in ("index.html", "membership.html", "object-detection.html"):
                    pg.screenshot(path=os.path.join(outdir, "desk-%s.png" % page_name), full_page=False)
                ctx.close()

                if shots and page_name == "index.html":
                    ctx2 = browser.new_context(viewport={"width": 390, "height": 844},
                                               device_scale_factor=2)
                    pg2 = ctx2.new_page()
                    pg2.goto("http://127.0.0.1:%d/index.html" % PORT, wait_until="networkidle")
                    pg2.screenshot(path=os.path.join(outdir, "mob-index.png"))
                    # 展开汉堡菜单再截一张
                    pg2.click("#nav-hamburger")
                    pg2.wait_for_timeout(400)
                    pg2.screenshot(path=os.path.join(outdir, "mob-menu.png"))
                    ctx2.close()

            browser.close()
    finally:
        httpd.shutdown()

    print()
    print("=" * 46)
    print("体检 %d 个页面，%d 个有问题" % (len(PAGES), bad_total))
    print("=" * 46)
    sys.exit(1 if bad_total else 0)


if __name__ == "__main__":
    main()
