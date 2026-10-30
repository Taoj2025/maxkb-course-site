#!/usr/bin/env python3
"""FDE 招聘数据实时刷新 —— 让 fde-jobs.html 的内容跟着市场一起变。

数据源（全部是公开、免登录的职位板接口）
──────────────────────────────────────────
国内
  · 智联招聘  sou.zhaopin.com         聚合站，页面里内嵌 __INITIAL_STATE__
  · 腾讯招聘  careers.tencent.com      官方 open api
海外
  · Greenhouse boards-api              anthropic / figma / datadog / stripe /
                                       netlify / twilio / cloudflare /
                                       squarespace / reddit / instacart /
                                       flexport / airbnb
  · Ashby posting-api                  openai / notion / linear / sentry /
                                       ramp / replit / supabase / railway /
                                       render / modal / posthog / ashbyhq

为什么没接 Boss 直聘 / 拉勾
──────────────────────────────────────────
两家都有强反爬：Boss 的 wapi 搜索接口要带签名 cookie（实测返回空列表），
拉勾的搜索页是纯 JS 渲染，HTML 里没有职位数据。定时硬啃既拿不到东西，
也违反对方的使用条款。国内这块改用智联聚合站 + 腾讯官方 API，
数据是真实在招的岗位，链接也点得开。

写到哪去
──────────────────────────────────────────
输出 SITE_DIR/data/fde-jobs.json。页面是浏览器端 fetch 这个文件，
而 /data/* 在 Vercel 侧是 rewrite 到源站的实时转发（must-revalidate），
所以这个文件一改，线上立刻变 —— 不用重新构建，不用发版。

设计要点（和 scripts/fetch-aihot.py 同一套思路）
──────────────────────────────────────────
  · 抓取失败**不覆盖**已有数据：单个源失败就少一个源，整体岗位数太少则整轮放弃
  · 统计口径（薪资分布 / 远程比例 / 城市分布 / 技能聚类）全部按实时数据重算，
    页面上写死的数字改成从 JSON 渲染
  · 原子写（临时文件 + os.replace），避免抓到一半的文件被读走

用法
──────────────────────────────────────────
  SITE_DIR=/var/www/maxkb-course-site python3 scripts/fde-daily/refresh_jobs.py
  python3 scripts/fde-daily/refresh_jobs.py --dry-run     # 只打印不写文件
"""

import json
import os
import re
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

SITE_DIR = Path(os.environ.get("SITE_DIR", Path(__file__).resolve().parent.parent.parent))
OUT_FILE = SITE_DIR / "data" / "fde-jobs.json"
CST = timezone(timedelta(hours=8))

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
TIMEOUT = 25
MAX_WORKERS = 8

# ── 海外职位板 ────────────────────────────────────────────────────────
# (token, 公司名, 是否 AI 公司, 是否重点公司)
GREENHOUSE = [
    ("anthropic", "Anthropic", True, True),
    ("openai", "OpenAI", True, True),        # OpenAI 用的是 Ashby，token 在下面
    ("figma", "Figma", False, False),
    ("datadog", "Datadog", False, False),
    ("stripe", "Stripe", False, False),
    ("netlify", "Netlify", False, False),
    ("twilio", "Twilio", False, False),
    ("cloudflare", "Cloudflare", False, True),
    ("squarespace", "Squarespace", False, False),
    ("reddit", "Reddit", False, False),
    ("instacart", "Instacart", False, False),
    ("flexport", "Flexport", False, False),
    ("airbnb", "Airbnb", False, False),
]

ASHBY = [
    ("openai", "OpenAI", True, True),
    ("notion", "Notion", False, False),
    ("linear", "Linear", False, False),
    ("sentry", "Sentry", False, False),
    ("ramp", "Ramp", False, False),
    ("replit", "Replit", False, False),
    ("supabase", "Supabase", False, False),
    ("railway", "Railway", False, False),
    ("render", "Render", False, False),
    ("modal", "Modal Labs", False, False),
    ("posthog", "PostHog", False, False),
    ("ashby", "Ashby", False, False),
]

# ── 国内 ──────────────────────────────────────────────────────────────
# 智联是聚合站，一个关键词一次请求；多几个关键词覆盖面更广
ZHAOPIN_KEYWORDS = ["FDE", "前端部署", "前端工程师", "全栈工程师",
                     "大模型应用工程师", "Serverless", "远程前端"]
TENCENT_URL = ("https://careers.tencent.com/tencentcareer/api/post/Query"
               "?timestamp=%d&keyword=%s&pageIndex=1&pageSize=30"
               "&language=zh-cn&area=cn")

# ── 岗位相关性过滤 ────────────────────────────────────────────────────
# 只留工程岗。招聘站上 90% 的岗位是销售/会计/法务，跟 FDE 没关系。
ENG_TITLE_KW = [
    "frontend", "front-end", "front end", "full stack", "full-stack",
    "fullstack", "software engineer", "software development", "web engineer",
    "platform engineer", "product engineer", "site reliability", "sre",
    "devops", "developer experience", "developer platform", "infrastructure",
    "solutions engineer", "application engineer", "edge engineer",
    "前端", "全栈", "研发", "开发工程师", "软件工程师", "大模型", "部署",
]
ENG_EXCLUDE_KW = [
    "sales", "account executive", "accountant", "accounting", "recruiter",
    "marketing", "legal", "nurse", "technician", "intern,", "pharmac",
    "销售", "商务", "会计", "财务", "法务", "招聘", "运营", "客服", "市场",
]
# 国内还要额外命中 —— 「前端工程师」之外，AI 应用 / 平台工程师也算 FDE 邻域
DOMESTIC_EXTRA_KW = ["前端", "fde", "全栈", "部署", "大模型", "智能体",
                     "serverless", "edge", "node", "react", "vue", "架构"]

AI_KW = ["ai", "ml", "llm", "gpt", "claude", "gemini", "agent", "copilot",
         "machine learning", "artificial intelligence", "大模型", "智能体",
         "人工智能", "深度学习", "aigc", "rag", "模型"]

# ── 技能聚类（教学结构固定，数量按实时数据重算）────────────────────────
# 聚类直接按「标签名」分组，不是按原始关键词 —— 这样标签怎么抽、聚类怎么算
# 用的是同一套名字，不会出现「检测出 Tailwind / CSS-in-JS，聚类里却叫
# Tailwind」这种对不上的情况。
SKILL_CLUSTERS = [
    ("🚀 核心前端框架", [
        "JavaScript", "TypeScript", "React", "Next.js", "Vue / Nuxt",
        "Svelte / Solid", "Remix / Angular", "全栈 Full-Stack", "微前端",
    ]),
    ("⚡ 部署 / 边缘运行时", [
        "构建工具", "CI/CD", "Serverless", "Edge 边缘计算", "CDN / Workers",
        "Vercel / Netlify", "Linux / Nginx", "Docker 容器化", "Kubernetes",
    ]),
    ("🛠️ 工程化能力", [
        "Node.js", "Python", "Go", "Rust / Java", "Git", "Monorepo",
        "可观测性", "自动化测试", "性能优化", "GraphQL", "gRPC",
        "Streaming / SSE", "数据库",
    ]),
    ("🤖 AI 时代新能力", [
        "LLM 应用", "AI/ML", "Agent 智能体", "RAG / 向量库", "Prompt 工程",
        "WebGPU / Wasm",
    ]),
    ("🎨 UX / 设计系统", [
        "CSS / Tailwind", "Design System", "Storybook", "可访问性 a11y",
        "UI / UX",
    ]),
    ("📚 知识要求（必须懂）", [
        "HTTP / TLS", "DNS", "Web 安全", "浏览器渲染", "开放平台 / API",
        "跨端", "DevEx 开发者体验", "Forward Deployed",
    ]),
]

# 智联/Ashby 给的原始技能名 → 本站的标签体系
RAW_TAG_MAP = {
    "html": "CSS / Tailwind", "html5": "CSS / Tailwind",
    "css": "CSS / Tailwind", "css3": "CSS / Tailwind",
    "javascript": "JavaScript", "js": "JavaScript", "es6": "JavaScript",
    "typescript": "TypeScript", "ts": "TypeScript",
    "react": "React", "reactjs": "React", "react.js": "React",
    "next": "Next.js", "nextjs": "Next.js", "next.js": "Next.js",
    "vue": "Vue / Nuxt", "vue.js": "Vue / Nuxt", "vuejs": "Vue / Nuxt",
    "nuxt": "Vue / Nuxt", "nuxt.js": "Vue / Nuxt",
    "angular": "Remix / Angular", "angularjs": "Remix / Angular",
    "svelte": "Svelte / Solid", "solidjs": "Svelte / Solid",
    "node": "Node.js", "node.js": "Node.js", "nodejs": "Node.js",
    "python": "Python", "py": "Python",
    "java": "Rust / Java", "golang": "Go", "go": "Go",
    "rust": "Rust / Java", "c++": "Rust / Java", "php": "Rust / Java",
    "小程序": "跨端", "react native": "跨端", "flutter": "跨端",
    "微前端": "微前端", "全栈": "全栈 Full-Stack", "前端": "前端 Frontend",
    "serverless": "Serverless", "kubernetes": "Kubernetes", "k8s": "Kubernetes",
    "docker": "Docker 容器化", "容器": "Docker 容器化",
    "linux": "Linux / Nginx", "nginx": "Linux / Nginx", "运维": "Linux / Nginx",
    "git": "Git", "svn": "Git",
    "mysql": "数据库", "postgresql": "数据库", "redis": "数据库",
    "mongodb": "数据库", "oracle": "数据库",
    "性能优化": "性能优化", "测试": "自动化测试", "单元测试": "自动化测试",
    "graphql": "GraphQL", "grpc": "gRPC", "websocket": "Streaming / SSE",
    "tailwind": "CSS / Tailwind", "sass": "CSS / Tailwind",
    "设计系统": "Design System", "storybook": "Storybook",
    "a11y": "可访问性 a11y", "无障碍": "可访问性 a11y",
    "大模型": "LLM 应用", "llm": "LLM 应用", "agent": "Agent 智能体",
    "智能体": "Agent 智能体", "rag": "RAG / 向量库", "向量": "RAG / 向量库",
    "人工智能": "AI/ML", "机器学习": "AI/ML", "深度学习": "AI/ML",
    "prompt": "Prompt 工程", "提示词": "Prompt 工程",
    "wasm": "WebGPU / Wasm", "webassembly": "WebGPU / Wasm",
    "http": "HTTP / TLS", "https": "HTTP / TLS", "tcp": "HTTP / TLS",
    "dns": "DNS", "cdn": "CDN / Workers",
    "安全": "Web 安全", "xss": "Web 安全", "cors": "Web 安全",
    "浏览器": "浏览器渲染", "渲染": "浏览器渲染",
    "开放平台": "开放平台 / API", "api": "开放平台 / API", "sdk": "开放平台 / API",
    "ui": "UI / UX", "ux": "UI / UX", "交互": "UI / UX", "用户研究": "UI / UX",
    "vue3": "Vue / Nuxt", "webpack": "构建工具", "vite": "构建工具",
    "rollup": "构建工具", "turbopack": "构建工具", "esbuild": "构建工具",
    "webpack5": "构建工具", "jenkins": "CI/CD", "gitlab": "CI/CD",
    "监控": "可观测性", "可观测": "可观测性", "日志": "可观测性",
    "edge": "Edge 边缘计算", "边缘": "Edge 边缘计算",
    "vercel": "Vercel / Netlify", "netlify": "Vercel / Netlify",
    "cloudflare": "CDN / Workers", "workers": "CDN / Workers",
    "monorepo": "Monorepo", "typescript ": "TypeScript",
}

# 智联的原始 tag 里混着「项目经验」和「学历」，不是技能，过滤掉
RAW_TAG_JUNK = re.compile(
    r"项目|本科|硕士|大专|学历|应届|实习经验|在校生|经验$|规模|融资|行业|"
    r"经验|描述|其他$|语言$|教材|课程|证书")

# ── 薪资分桶 ──────────────────────────────────────────────────────────
# (桶名, 展示区间, 颜色, 下界, 上界)  —— 国内按月薪(元)，海外按年薪(美元)
DOMESTIC_SALARY_BUCKETS = [
    ("Junior（应届 / 1-3 年）", "10K 以下", "#10B981", 0, 10000),
    ("Mid（3-5 年）", "10-20K", "#3B82F6", 10000, 20000),
    ("Senior（5-8 年）", "20-30K", "#8B5CF6", 20000, 30000),
    ("Staff（8 年+）", "30-50K", "#F59E0B", 30000, 50000),
    ("Principal / 专家", "50K 以上", "#EF4444", 50000, 10 ** 9),
]
OVERSEAS_SALARY_BUCKETS = [
    ("Mid", "$100K 以下", "#10B981", 0, 100000),
    ("Senior", "$100-150K", "#3B82F6", 100000, 150000),
    ("Staff", "$150-200K", "#8B5CF6", 150000, 200000),
    ("Principal", "$200-300K", "#F59E0B", 200000, 300000),
    ("Distinguished / 专家", "$300K+", "#EF4444", 300000, 10 ** 9),
]

# 城市名归一（只处理常见写法，认不出来就原样用）
CITY_ALIAS = {
    "san francisco": "SF / Bay Area", "san francisco, ca": "SF / Bay Area",
    "sf": "SF / Bay Area", "palo alto": "SF / Bay Area",
    "new york": "NYC", "new york, ny": "NYC", "nyc": "NYC",
    "seattle": "Seattle / Redmond", "seattle, wa": "Seattle / Redmond",
    "redmond": "Seattle / Redmond", "bellevue": "Seattle / Redmond",
    "boston": "Boston", "austin": "Austin", "denver": "Denver",
    "los angeles": "LA", "london": "London", "dublin": "Dublin",
    "berlin": "Berlin", "toronto": "Toronto", "vancouver": "Vancouver",
    "北京": "北京", "上海": "上海", "深圳": "深圳", "广州": "广州",
    "杭州": "杭州", "成都": "成都", "南京": "南京", "武汉": "武汉",
    "西安": "西安", "苏州": "苏州", "厦门": "厦门", "长沙": "长沙",
    "合肥": "合肥", "青岛": "青岛", "济南": "济南", "天津": "天津",
    "重庆": "重庆", "郑州": "郑州", "remote": "Remote (Global)",
    "global": "Remote (Global)", "worldwide": "Remote (Global)",
}

_print_lock = threading.Lock()


def log(msg):
    with _print_lock:
        print(msg, flush=True)


def http_get(url, headers=None, retries=2):
    """带重试的 GET。失败返回 None，不抛异常 —— 单个源挂掉不能拖垮整轮。"""
    h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*"}
    h.update(headers or {})
    for attempt in range(retries + 1):
        try:
            req = Request(url, headers=h)
            with urlopen(req, timeout=TIMEOUT) as r:
                return r.read().decode("utf-8", "replace")
        except HTTPError as e:
            if e.code in (429, 502, 503, 504) and attempt < retries:
                continue
            return None
        except (URLError, OSError, TimeoutError):
            if attempt < retries:
                continue
            return None
    return None


# ── 海外：Greenhouse ──────────────────────────────────────────────────
def fetch_greenhouse(token, company, is_ai, premium):
    # content=false 是不带职位正文的意思 —— Anthropic 带正文是 9.8MB，
    # 不带只有 480KB，我们只要标题/地点/链接
    url = "https://boards-api.greenhouse.io/v1/boards/%s/jobs?content=false" % token
    txt = http_get(url)
    if not txt:
        return None
    try:
        jobs = json.loads(txt).get("jobs", [])
    except ValueError:
        return None

    out = []
    for j in jobs:
        title = (j.get("title") or "").strip()
        if not title or not is_eng_title(title):
            continue
        loc = (j.get("location") or {}).get("name") or ""
        loc = loc.split(" | ")[0].strip() or "Remote"
        # Greenhouse 的 content=false 不带正文，只有部门/团队等 metadata
        meta = " ".join(str(v) for v in (j.get("metadata") or []))
        all_tags = derive_tags(title, meta)
        out.append(make_card(
            company=company, title=title,
            salary="面议（该公司不公开薪资）",
            city=loc,
            tags=all_tags[:6],
            level=guess_level(title),
            remote=is_remote(loc, j.get("metadata")),
            source="%s Careers" % company,
            url=j.get("absolute_url") or "",
            premium=premium, is_ai=is_ai or looks_ai(title),
            all_tags=all_tags,
        ))
    return out


# ── 海外：Ashby ───────────────────────────────────────────────────────
def fetch_ashby(token, company, is_ai, premium):
    url = ("https://api.ashbyhq.com/posting-api/job-board/%s"
           "?includeCompensation=true" % token)
    txt = http_get(url)
    if not txt:
        return None
    try:
        jobs = json.loads(txt).get("jobs", [])
    except ValueError:
        return None

    out = []
    for j in jobs:
        if j.get("isListed") is False:
            continue
        title = (j.get("title") or "").strip()
        if not title or not is_eng_title(title):
            continue
        loc = (j.get("location") or "").strip()
        secondary = j.get("secondaryLocations") or []
        if len(secondary) > 1:
            loc = "%s / %s" % (loc, secondary[1].get("location", ""))
        if not loc:
            loc = "Remote"
        salary, sal_lo, sal_hi = parse_ashby_comp(j.get("compensation"))
        # 描述里有完整的技术栈要求，是最准的技能来源
        desc = (j.get("descriptionPlain") or "")[:3000]
        dept = " ".join(x for x in (j.get("department"), j.get("team")) if x)
        all_tags = derive_tags(title, desc + " " + dept)
        out.append(make_card(
            company=company, title=title,
            salary=salary,
            city=loc,
            tags=all_tags[:6],
            level=guess_level(title),
            remote=bool(j.get("isRemote")) or is_remote(loc, None),
            source="%s Careers" % company,
            url=j.get("jobUrl") or j.get("applyUrl") or "",
            premium=premium, is_ai=is_ai or looks_ai(title),
            salary_lo=sal_lo, salary_hi=sal_hi,
            all_tags=all_tags,
            published=j.get("publishedAt") or "",
        ))
    return out


# ── 国内：智联招聘 ────────────────────────────────────────────────────
def fetch_zhaopin(keyword):
    url = "https://sou.zhaopin.com/?" + urlencode({"kw": keyword})
    txt = http_get(url)
    if not txt:
        return None
    i = txt.find("__INITIAL_STATE__=")
    if i < 0:
        return None
    j = txt.find("{", i)
    if j < 0:
        return None
    try:
        state, _ = json.JSONDecoder().raw_decode(txt[j:])
    except ValueError:
        return None

    out = []
    seen = set()
    for p in state.get("positionList") or []:
        name = (p.get("name") or "").strip()
        company = (p.get("companyName") or "").strip()
        if not name or not company:
            continue
        if name in seen:
            continue
        seen.add(name)
        if not is_domestic_eng(name, (p.get("jobSummary") or "")
                               + (p.get("subJobTypeLevelName") or "")):
            continue
        salary_txt, sal_lo, sal_hi = parse_cn_salary(p)
        # 智联的 jobSkillTags 是官方技能标签，最准；showSkillTags 混着学历之类，用前者就够
        skills = [t.get("name") for t in (p.get("jobSkillTags") or [])
                  if t.get("name")]
        extra = " ".join(skills)
        city = (p.get("workCity") or "").strip()
        district = (p.get("cityDistrict") or "").strip()
        full_city = "%s %s" % (city, district) if district and district != city else city
        exp = (p.get("workingExp") or "").strip()
        all_tags = derive_tags(name, extra, raw_tags=skills)
        # 智联的搜索结果里没有远程标记，只能从标题文字判断
        is_remote_cn = "远程" in name or "远程" in (p.get("workMode") or "")
        out.append(make_card(
            company=company, title=name,
            salary=salary_txt,
            city=full_city or "全国",
            tags=all_tags[:6],
            level=cn_level(exp),
            remote=is_remote_cn,
            source="智联招聘",
            url=p.get("positionUrl") or p.get("positionURL") or "",
            premium=False,
            is_ai=looks_ai(name + " " + extra),
            salary_lo=sal_lo, salary_hi=sal_hi,
            all_tags=all_tags,
            published=p.get("publishTime") or "",
        ))
    return out


# ── 国内：腾讯招聘 ────────────────────────────────────────────────────
def fetch_tencent(keyword="FDE"):
    url = TENCENT_URL % (int(datetime.now().timestamp() * 1000), quote(keyword))
    txt = http_get(url)
    if not txt:
        return None
    try:
        data = json.loads(txt).get("Data") or {}
    except ValueError:
        return None

    out = []
    for p in data.get("Posts") or []:
        name = (p.get("RecruitPostName") or "").strip()
        if not name:
            continue
        if not is_domestic_eng(name, (p.get("CategoryName") or "")):
            continue
        city = (p.get("LocationName") or "").strip()
        dept = (p.get("BGName") or "") + " " + (p.get("CategoryName") or "")
        all_tags = derive_tags(name, dept)
        out.append(make_card(
            company=(p.get("ComName") or "腾讯").strip(),
            title=name,
            salary="面议（官方招聘站不公开）",
            city=city or "全国",
            tags=all_tags[:6],
            level=cn_level(""),
            remote=False,
            source="腾讯招聘",
            url=p.get("PostURL") or "",
            premium=True,
            is_ai=looks_ai(name + " " + dept),
            all_tags=all_tags,
            published=p.get("LastUpdateTime") or "",
        ))
    return out


# ── 工具函数 ──────────────────────────────────────────────────────────
def is_eng_title(title):
    t = title.lower()
    if any(k in t for k in ENG_EXCLUDE_KW):
        return False
    return any(k in t for k in ENG_TITLE_KW)


def is_domestic_eng(title, extra=""):
    blob = (title + " " + extra).lower()
    if any(k in blob for k in ENG_EXCLUDE_KW):
        return False
    return any(k.lower() in blob for k in DOMESTIC_EXTRA_KW)


def looks_ai(text):
    t = text.lower()
    return any(k in t for k in AI_KW)


def is_remote(loc, metadata):
    t = (loc or "").lower()
    if "remote" in t or "global" in t or "worldwide" in t or "anywhere" in t:
        return True
    for m in metadata or []:
        v = str(m).lower()
        if "remote" in v:
            return True
    return False


def guess_level(title):
    t = title.lower()
    for key, name in [("principal", "Principal"), ("staff", "Staff"),
                      ("senior", "Senior"), ("lead", "Lead"),
                      ("principal", "Principal"), ("junior", "Junior"),
                      ("intern", "Intern"), ("entry", "Entry"),
                      ("associate", "Associate")]:
        if key in t:
            return name
    return ""


def cn_level(exp):
    if not exp:
        return ""
    if "应届" in exp or "1年以下" in exp:
        return "Junior"
    if "1-3" in exp or "3-5" in exp:
        return "Mid"
    if "5-10" in exp or "10年以上" in exp:
        return "Senior"
    return ""


def derive_tags(title, text="", raw_tags=()):
    """检测岗位需要的技能标签。

    title  职位名（权重最高，始终参与匹配）
    text   职位描述 / 部门 / 分类等补充文本
    raw_tags  数据源直接给的技能名列表（智联的 jobSkillTags），这些最准

    返回完整标签列表（不截断）—— 卡片上只显示前 6 个，
    但统计聚类要用全量，否则排在第 7 以后的技能会被凭空抹掉。
    """
    blob = (title + " " + text).lower()
    hits = []
    for pat, name in TAG_PATTERNS:
        if name not in hits and re.search(pat, blob):
            hits.append(name)
    # 数据源自带的技能名 → 映射到本站标签体系
    for raw in raw_tags or ():
        raw = (raw or "").strip()
        if not raw or len(raw) > 20 or RAW_TAG_JUNK.search(raw):
            continue
        mapped = RAW_TAG_MAP.get(raw.lower().strip())
        if mapped and mapped not in hits:
            hits.append(mapped)
    return hits


# 正则 → 标签。顺序即优先级（靠前的先命中）。
TAG_PATTERNS = [
    (r"forward[ -]?deployed|\bfde\b|前置部署", "Forward Deployed"),
    (r"developer experience|\bdevex\b|开发者体验", "DevEx 开发者体验"),
    (r"full[ -]?stack|\bfullstack\b|全栈", "全栈 Full-Stack"),
    (r"front[ -]?end|\bfrontend\b|\bweb engineer\b|前端", "前端 Frontend"),
    (r"\breact\b", "React"),
    (r"\btypescript\b", "TypeScript"),
    (r"\bnext\.?js\b|\bnextjs\b", "Next.js"),
    (r"\bvue\b|\bnuxt\b", "Vue / Nuxt"),
    (r"\bsvelte\b|\bsolid\b", "Svelte / Solid"),
    (r"\bremix\b|\bangular\b", "Remix / Angular"),
    (r"\bnode\.?js\b|\bnodejs\b", "Node.js"),
    (r"\bpython\b", "Python"),
    (r"\bgolang\b|\bgo\b", "Go"),
    (r"\brust\b|\bjava\b", "Rust / Java"),
    (r"\bgraphql\b", "GraphQL"),
    (r"\bgrpc\b|\bprotobuf\b", "gRPC"),
    (r"\bwebsocket\b|\bsse\b|\bstreaming\b", "Streaming / SSE"),
    (r"\bmicro[ -]?frontend|微前端", "微前端"),
    (r"\bvite\b|\bwebpack\b|\bturbopack\b|\brollup\b|\besbuild\b", "构建工具"),
    (r"\bci[/-]?cd\b|\bjenkins\b|\bgithub actions\b|\bcircleci\b|\b流水线\b", "CI/CD"),
    (r"\bdocker\b|\bcontainer|容器化", "Docker 容器化"),
    (r"\bkubernetes\b|\bk8s\b", "Kubernetes"),
    (r"\bserverless\b|\blambda\b|云函数|无服务器", "Serverless"),
    (r"\bedge\b|边缘计算|edge function", "Edge 边缘计算"),
    (r"\bworkers\b|\bcloudflare\b|\bcdn\b", "CDN / Workers"),
    (r"\bvercel\b|\bnetlify\b", "Vercel / Netlify"),
    (r"\bnginx\b|\blinux\b|运维", "Linux / Nginx"),
    (r"\bgit\b", "Git"),
    (r"\bmonorepo\b", "Monorepo"),
    (r"\btailwind\b|\bsass\b|\bstyled-components\b|\bcss\b", "CSS / Tailwind"),
    (r"design system|设计系统", "Design System"),
    (r"\bstorybook\b", "Storybook"),
    (r"\ba11y\b|accessibility|可访问性", "可访问性 a11y"),
    (r"\bperformance\b|性能优化|web vitals|首屏", "性能优化"),
    (r"\bobservability\b|\bmonitoring\b|可观测|监控", "可观测性"),
    (r"\btesting\b|\bjest\b|\bplaywright\b|\bcypress\b|自动化测试|测试工程", "自动化测试"),
    (r"\bllm\b|\bgpt\b|\bclaude\b|\bgemini\b|大模型|生成式", "LLM 应用"),
    (r"\bagent\b|智能体|\bcopilot\b", "Agent 智能体"),
    (r"\brag\b|向量库|\bembedding\b|检索增强", "RAG / 向量库"),
    (r"\bprompt\b|提示词", "Prompt 工程"),
    (r"\bwebgpu\b|\bwasm\b|\bwebassembly\b", "WebGPU / Wasm"),
    (r"\bhttp\b|\bhttps\b|\btls\b|协议", "HTTP / TLS"),
    (r"\bdns\b", "DNS"),
    (r"\bcors\b|\bxss\b|\bcsrf\b|安全", "Web 安全"),
    (r"\bbrowser\b|浏览器|渲染", "浏览器渲染"),
    (r"\bmobile\b|\bflutter\b|\breact native\b|小程序|跨端", "跨端"),
    (r"\bopenapi\b|\bsdk\b|开放平台|接口", "开放平台 / API"),
    (r"\bmysql\b|\bpostgres|\bredis\b|\bmongodb\b|\boracle\b|数据库", "数据库"),
    (r"\bui\b|\bux\b|\buser research\b|\binteraction\b|交互设计|用户研究", "UI / UX"),
]


# FDE 相关度打分 —— 决定一个岗位值不值得放上页面
RELEVANCE_PATTERNS = [
    # 标题里直接写着 Forward Deployed 的，权重给足 ——
    # 不然一个描述里顺带提了句 frontend 的「Founding Software Engineer」
    # 会排到真正的 FDE 岗位前面去。
    (r"forward[ -]?deployed|\bfde\b|前置部署", 200),
    (r"developer experience|\bdevex\b|开发者体验", 60),
    (r"front[ -]?end|\bfrontend\b|\bweb engineer\b|前端", 40),
    (r"full[ -]?stack|\bfullstack\b|全栈", 35),
    (r"platform engineer|平台工程师", 30),
    (r"site reliability|\bsre\b|\bdevops\b|\breliability\b", 25),
    (r"\bweb\b|\bapi\b|\binterface\b|开放平台", 20),
    (r"software engineer|工程师|研发", 15),
    (r"\bapplication engineer\b|\bsolutions engineer\b", 12),
    (r"\bui\b|\bux\b|\bdesign\b|设计", 10),
]


def relevance_score(job):
    blob = (job["title"] + " " + " ".join(job.get("_alltags") or job.get("tags") or [])).lower()
    score = sum(w for pat, w in RELEVANCE_PATTERNS if re.search(pat, blob))
    if job.get("premium"):
        score += 30          # 顶级公司优先（Anthropic / OpenAI / Cloudflare …）
    if job.get("ai_era"):
        score += 10          # AI 时代岗位其次
    return score



def make_card(company, title, salary, city, tags, level, remote, source,
              url, premium, is_ai, salary_lo=None, salary_hi=None,
              published="", all_tags=None):
    return {
        "company": company,
        "title": title,
        "salary": salary,
        "city": city,
        "tags": tags,
        "level": level,
        "remote": bool(remote),
        "source": source,
        "url": url,
        "premium": bool(premium),
        "ai_era": bool(is_ai),
        "_lo": salary_lo,
        "_hi": salary_hi,
        "_published": published,
        "_alltags": all_tags or tags,
    }


def parse_cn_salary(p):
    """智联的薪资：salary60='1.3-2万' / salaryReal='13001-20000'（月薪，元）。"""
    real = p.get("salaryReal") or ""
    lo = hi = None
    m = re.match(r"(\d+)-(\d+)", str(real))
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
    txt = (p.get("salary60") or "").strip()
    if not txt and lo:
        txt = "%d-%dK" % (round(lo / 1000), round(hi / 1000))
    if not txt:
        txt = "面议"
    return txt, lo, hi


def parse_ashby_comp(comp):
    """Ashby 的薪资结构：compensationTiers[].components[] 里是 minValue/maxValue。"""
    if not comp:
        return "面议", None, None
    summary = comp.get("scrapeableCompensationSalarySummary") or ""
    lo = hi = None
    for tier in comp.get("compensationTiers") or []:
        for c in tier.get("components") or []:
            if c.get("compensationType") != "Salary":
                continue
            mv, xv = c.get("minValue"), c.get("maxValue")
            if mv is None and xv is None:
                continue
            lo = mv if lo is None else min(lo, mv)
            hi = xv if hi is None else max(hi, xv)
    if lo is not None and hi is not None:
        summary = "$%dK – $%dK" % (round(lo / 1000), round(hi / 1000))
    elif summary:
        summary = summary.replace("USD", "").strip()
    else:
        summary = "面议"
    return summary, lo, hi


def norm_city(city):
    c = (city or "").strip()
    if not c:
        return "其他"
    low = c.lower()
    if "remote" in low:
        return "Remote (Global)"
    for k, v in CITY_ALIAS.items():
        if low == k or low.startswith(k + ",") or low.startswith(k + " "):
            return v
    # 「北京 海淀」这种带空格的后缀
    head = c.split()[0] if " " in c and not c[:1].isascii() else c
    return CITY_ALIAS.get(head.lower(), head)


def build_salary_distribution(jobs, overseas):
    """按薪资中位数分桶。百分比一律以「该组岗位总数」为分母，
    这样所有桶加起来正好 100%（含「未公开薪资」那一档）。"""
    buckets = OVERSEAS_SALARY_BUCKETS if overseas else DOMESTIC_SALARY_BUCKETS
    total = len(jobs) or 1
    with_salary = [j for j in jobs
                   if j.get("_lo") is not None and j.get("_hi") is not None]
    out = []
    for label, rng, color, lo, hi in buckets:
        n = sum(1 for j in with_salary if lo <= ((j["_lo"] + j["_hi"]) / 2) < hi)
        out.append({"level": label, "range": rng,
                    "percent": round(n * 100.0 / total), "color": color})
    if len(with_salary) < total:
        out.append({
            "level": "未公开薪资", "range": "—",
            "percent": round((total - len(with_salary)) * 100.0 / total),
            "color": "#9CA3AF",
        })
    return out


def strip_internal(jobs):
    """去掉 _lo / _hi / _published 这些只在计算阶段用的内部字段。"""
    return [{k: v for k, v in j.items() if not k.startswith("_")} for j in jobs]



def build_skill_clusters(jobs):
    """6 大技能聚类。

    聚类成员按「标签名」判定（不是关键词子串匹配）—— 检测和统计用同一套
    名字，才不会出现「标签叫 Tailwind / CSS-in-JS、聚类里叫 Tailwind」
    这种对不上的情况。标题里出现的技能名也计入。
    """
    clusters = []
    for name, tag_names in SKILL_CLUSTERS:
        counts = {}
        matched = 0
        for j in jobs:
            tags = set(j.get("_alltags") or j.get("tags") or [])
            low_title = j["title"].lower()
            hit = False
            for t in tag_names:
                if t in tags:
                    counts[t] = counts.get(t, 0) + 1
                    hit = True
                elif t.lower().split(" /")[0].lower() in low_title:
                    counts[t] = counts.get(t, 0) + 1
                    hit = True
            if hit:
                matched += 1
        if not matched:
            continue
        skills = [{"name": t, "count": counts[t],
                   "percent": round(counts[t] * 100.0 / matched)}
                  for t in tag_names if counts.get(t)]
        skills.sort(key=lambda s: (-s["count"], s["name"]))
        clusters.append({"name": name, "total": matched, "skills": skills[:8]})
    return clusters


def build_remote_ratio(domestic, overseas):
    d_remote = sum(1 for j in domestic if j["remote"])
    o_remote = sum(1 for j in overseas if j["remote"])
    d_pct = round(d_remote * 100.0 / len(domestic), 1) if domestic else 0
    o_pct = round(o_remote * 100.0 / len(overseas), 1) if overseas else 0
    return {
        "domestic_remote_jobs": d_remote,
        "domestic_total": len(domestic),
        "domestic_remote_percent": d_pct,
        "overseas_remote_jobs": o_remote,
        "overseas_total": len(overseas),
        "overseas_remote_percent": o_pct,
        "comment": "海外 %s%% 职位支持远程 · 国内 %s%%（按实时招聘数据统计）"
                   % (o_pct, d_pct),
    }


def build_city_distribution(domestic, overseas):
    def top(jobs, n):
        counts = {}
        for j in jobs:
            c = norm_city(j["city"])
            counts[c] = counts.get(c, 0) + 1
        items = sorted(counts.items(), key=lambda kv: -kv[1])[:n]
        total = len(jobs) or 1
        return [{"city": c, "jobs": n, "percent": round(n * 100.0 / total, 1)}
                for c, n in items]

    return {"domestic_top10": top(domestic, 10),
            "overseas_top5": top(overseas, 5)}


def build_summary(domestic, overseas):
    d_companies = len({j["company"] for j in domestic})
    o_companies = len({j["company"] for j in overseas})
    ai_companies = len({j["company"] for j in domestic + overseas if j["ai_era"]})
    d_sal = [((j["_lo"] + j["_hi"]) / 2) for j in domestic
             if j.get("_lo") is not None]
    o_sal = [((j["_lo"] + j["_hi"]) / 2) for j in overseas
             if j.get("_lo") is not None]
    return {
        "total_companies": d_companies + o_companies,
        "domestic_companies": d_companies,
        "overseas_companies": o_companies,
        "ai_companies": ai_companies,
        "total_jobs_estimated": len(domestic) + len(overseas),
        "domestic_jobs": len(domestic),
        "overseas_jobs": len(overseas),
        "avg_salary_domestic": ("%dK" % round(sum(d_sal) / len(d_sal) / 1000))
                               if d_sal else "—",
        "avg_salary_overseas": ("$%dK" % round(sum(o_sal) / len(o_sal) / 1000))
                               if o_sal else "—",
    }


# ── 主流程 ────────────────────────────────────────────────────────────
# 每个职位板算一个「源」，页面上「数据源状态」卡片按源显示。
SOURCE_META = {
    "zhaopin":   {"name": "智联招聘", "icon": "💼",
                  "detail": "公开搜索结果 · 免登录实时抓取"},
    "tencent":   {"name": "腾讯招聘", "icon": "🔵",
                  "detail": "官方开放 API · 实时"},
    "greenhouse": {"name": "Greenhouse 职位板", "icon": "🌿",
                   "detail": "12 家海外公司的公开招聘 API"},
    "ashby":     {"name": "Ashby 职位板", "icon": "🧩",
                  "detail": "12 家公司的公开招聘 API · 含 OpenAI"},
}


def collect():
    """并发抓所有数据源。返回 (国内职位, 海外职位, 各源状态)。"""
    status = {}
    results = {}

    def run(group, name, fn):
        try:
            jobs = fn()
        except Exception as e:                       # 兜底，别让一个源炸掉整轮
            jobs = None
            log("   ❌ %-22s 异常：%s" % (name, str(e)[:70]))
        if jobs is None:
            st = status.setdefault(group, {"ok": False, "count": 0, "boards": {}})
            st["boards"][name] = 0
            log("   ⚠️ %-22s 抓取失败" % name)
            return None
        st = status.setdefault(group, {"ok": True, "count": 0, "boards": {}})
        st["ok"] = True
        st["count"] += len(jobs)
        st["boards"][name] = len(jobs)
        log("   ✅ %-22s %d 个岗位" % (name, len(jobs)))
        return jobs

    tasks = []

    # 国内 —— 智联多关键词并发
    for kw in ZHAOPIN_KEYWORDS:
        def _z(kw=kw):
            return run("zhaopin", "智联·%s" % kw, lambda: fetch_zhaopin(kw))
        tasks.append(_z)
    tasks.append(lambda: run("tencent", "腾讯招聘", fetch_tencent))

    # 海外 —— Greenhouse
    for token, company, is_ai, premium in GREENHOUSE:
        if company == "OpenAI":          # OpenAI 用 Ashby，别重复抓
            continue
        def _g(t=token, c=company, a=is_ai, p=premium):
            return run("greenhouse", "%s Careers" % c,
                       lambda: fetch_greenhouse(t, c, a, p))
        tasks.append(_g)

    # 海外 —— Ashby
    for token, company, is_ai, premium in ASHBY:
        def _a(t=token, c=company, a=is_ai, p=premium):
            return run("ashby", "%s Careers" % c,
                       lambda: fetch_ashby(t, c, a, p))
        tasks.append(_a)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        for r in ex.map(lambda f: f(), tasks):
            if r:
                results[r[0]["source"]] = results.get(r[0]["source"], []) + r

    zhaopin_jobs = results.get("智联招聘", [])
    tencent_jobs = results.get("腾讯招聘", [])
    overseas = []
    for src, jobs in results.items():
        if src not in ("智联招聘", "腾讯招聘"):
            overseas.extend(jobs)

    # 去重（同一家公司同一个职位只留一条）
    def dedup(jobs):
        seen = set()
        out = []
        for j in jobs:
            k = (j["company"], j["title"], j["city"])
            if k in seen:
                continue
            seen.add(k)
            out.append(j)
        return out

    domestic = dedup(zhaopin_jobs + tencent_jobs)
    overseas = dedup(overseas)
    return domestic, overseas, status


def rank_and_cap(jobs, limit, per_company=0):
    """按 FDE 相关度排序后截断。per_company > 0 时限制单家公司占比，
    免得一个 200 岗位的 board 把整页刷成同一家公司。"""
    scored = sorted(jobs, key=lambda j: (-relevance_score(j), j["company"], j["title"]))
    if not per_company:
        return scored[:limit]
    out, per = [], {}
    for j in scored:
        c = j["company"]
        if per.get(c, 0) >= per_company:
            continue
        per[c] = per.get(c, 0) + 1
        out.append(j)
        if len(out) >= limit:
            break
    return out



def main():
    dry = "--dry-run" in sys.argv
    log("=" * 62)
    log("📊 FDE 招聘数据刷新 · %s" % datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S"))
    log("=" * 62)

    domestic, overseas, status = collect()

    log("")
    log("   抓到：国内 %d 个岗位 / %d 家公司 · 海外 %d 个岗位 / %d 家公司"
        % (len(domestic), len({j['company'] for j in domestic}),
           len(overseas), len({j['company'] for j in overseas})))

    # ── 安全闸：岗位太少就整轮放弃，宁可显示旧数据也不要打空 ──
    MIN_JOBS = 30
    old = {}
    if OUT_FILE.exists():
        try:
            old = json.loads(OUT_FILE.read_text(encoding="utf-8"))
        except ValueError:
            old = {}

    def old_jobs(key):
        dom = old.get("domestic") or {}
        if key == "overseas":
            return (old.get("overseas") or {}).get("jobs") or []
        return (dom.get(key) or {}).get("jobs") or []

    # 老版本用 boss/lagou 命名，新版改叫 zhaopin/tencent
    old_d = old_jobs("zhaopin") + old_jobs("boss") + old_jobs("tencent") + old_jobs("lagou")
    old_o = old_jobs("overseas")
    old_count = len(old_d) + len(old_o)

    if len(domestic) + len(overseas) < MIN_JOBS:
        log("")
        log("❌ 本轮只抓到 %d 个岗位（少于 %d），放弃覆盖，保留原有数据"
            % (len(domestic) + len(overseas), MIN_JOBS))
        return 1

    # ── 单边兜底：一边全挂时用旧数据顶上，页面不至于空掉 ──
    stale_domestic = False
    if not domestic and old_d:
        log("⚠️  国内源本轮全挂，沿用旧国内数据 %d 条" % len(old_d))
        domestic = old_d
        stale_domestic = True
    if not overseas and old_o:
        log("⚠️  海外源本轮全挂，沿用旧海外数据 %d 条" % len(old_o))
        overseas = old_o

    # ── 排序 + 限量 ──
    # 国内智联多、腾讯少：智联 24 条，腾讯全收（本来就只有十条上下）
    # 海外限制单家最多 3 条，否则一个 200 岗位的 board 会刷屏
    zhaopin_jobs = [j for j in domestic if j["source"] == "智联招聘"]
    tencent_jobs = [j for j in domestic if j["source"] == "腾讯招聘"]
    if not zhaopin_jobs:                       # 兜底旧数据里的来源标注
        zhaopin_jobs = domestic
    if not tencent_jobs:
        tencent_jobs = domestic

    zhaopin_jobs = rank_and_cap(zhaopin_jobs, 24)
    tencent_jobs = rank_and_cap(tencent_jobs, 12)
    overseas = rank_and_cap(overseas, 36, per_company=3)

    domestic = zhaopin_jobs + tencent_jobs

    # 统计用带 _lo/_hi 的完整对象，落盘前再剥掉内部字段
    stat_domestic = domestic
    stat_overseas = overseas
    zhaopin_jobs = strip_internal(zhaopin_jobs)
    tencent_jobs = strip_internal(tencent_jobs)
    overseas = strip_internal(overseas)
    domestic = zhaopin_jobs + tencent_jobs

    now = datetime.now(CST)
    updated_at = now.isoformat()

    sources_meta = []
    for key in ("zhaopin", "tencent", "greenhouse", "ashby"):
        st = status.get(key) or {"ok": False, "count": 0, "boards": {}}
        meta = dict(SOURCE_META[key])
        meta["key"] = key
        meta["ok"] = bool(st.get("ok"))
        meta["count"] = st.get("count", 0)
        meta["boards"] = st.get("boards", {})
        sources_meta.append(meta)

    data = {
        "version": "v3.0",
        "updated_at": updated_at,
        "source": "智联招聘 + 腾讯招聘 + Greenhouse + Ashby（公开职位板 API）",
        "live": True,
        "stale_domestic": stale_domestic,
        "summary": build_summary(stat_domestic, stat_overseas),
        "domestic": {
            "zhaopin": {
                "label": "🇨🇳 国内 · 智联招聘",
                "data_source": "智联招聘公开搜索结果（实时）",
                "jobs": zhaopin_jobs,
            },
            "tencent": {
                "label": "🔵 国内 · 腾讯招聘",
                "data_source": "腾讯招聘官方开放 API（实时）",
                "jobs": tencent_jobs,
            },
        },
        "overseas": {
            "label": "🌏 海外 · 顶级公司 careers",
            "data_source": "Greenhouse / Ashby 公开职位板（实时）",
            "fetched_at": updated_at,
            "jobs": overseas,
        },
        "skills": build_skill_clusters(stat_domestic + stat_overseas),
        "salary_distribution": {
            "domestic": build_salary_distribution(stat_domestic, overseas=False),
            "overseas": build_salary_distribution(stat_overseas, overseas=True),
        },
        "remote_ratio": build_remote_ratio(stat_domestic, stat_overseas),
        "city_distribution": build_city_distribution(stat_domestic, stat_overseas),
        "data_sources_meta": {
            "fetched_at": updated_at,
            "sources": sources_meta,
            "total_sources": len(sources_meta),
            "ok_sources": sum(1 for s in sources_meta if s["ok"]),
        },
    }

    if dry:
        log("")
        log("🧪 --dry-run：只打印不写文件")
        print(json.dumps(data["summary"], ensure_ascii=False, indent=2))
        print(json.dumps(data["remote_ratio"], ensure_ascii=False, indent=2))
        print("国内智联 %d · 腾讯 %d · 海外 %d"
              % (len(zhaopin_jobs), len(tencent_jobs), len(overseas)))
        for c in data["skills"]:
            print("  %-20s %d 岗位 · %s" % (c["name"], c["total"],
                                            ", ".join("%s %d%%" % (s["name"], s["percent"])
                                                      for s in c["skills"][:4])))
        print("样例：")
        for j in (zhaopin_jobs[:2] + tencent_jobs[:1] + overseas[:3]):
            print("  [%s] %s · %s · %s · %s · %s"
                  % (j["source"], j["company"], j["title"][:40],
                     j["salary"], j["city"], " / ".join(j["tags"][:4])))
        return 0

    # ── 原子写 ──
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False,
                                       dir=str(OUT_FILE.parent), suffix=".tmp")
    try:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp.close()
        os.replace(tmp.name, OUT_FILE)
    except Exception:
        tmp.close()
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)
        raise

    log("")
    log("✅ 已写入 %s" % OUT_FILE)
    log("   国内智联 %d · 腾讯 %d · 海外 %d（合计 %d）"
        % (len(zhaopin_jobs), len(tencent_jobs), len(overseas), len(domestic) + len(overseas)))
    log("   数据源：%d/%d 正常%s"
        % (data["data_sources_meta"]["ok_sources"],
           data["data_sources_meta"]["total_sources"],
           ("，上一版 %d 个岗位" % old_count) if old_count else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
