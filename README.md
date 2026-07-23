# MaxKB FDE 教学网站

> 基于 1Panel-dev/MaxKB 的开源企业级智能体平台教学课程
> 紫色 AI 科技风 · FDE 实战导向 · 师生混合受众

## 🌐 访问地址

部署到 GitHub Pages 后可访问：
```
https://<GitHub用户名>.github.io/maxkb-course-site/
```

## 📚 课程内容

- **理论基座**（PART 1）：MaxKB / RAG / LangChain / Workflow / MCP / Agent
- **6 步实操**（PART 2）：Docker 部署 → 模型接入 → 知识库 → 应用调试 → 发布嵌入
- **5 大场景**（PART 3）：高校客服 / 教师备课 / 文献精读 / 企业知识库 / 医院导诊

## 🎯 目标受众

- 学生：1 周搭出可演示项目
- 同行教师：把 AI 落地到自己的课程/班级
- 企业项目：交付客服/HR/导诊等垂直场景

## 🛠️ 技术栈

- HTML5 + CSS3 + Vanilla JavaScript（无框架）
- 紫色 AI 科技风（#5B2EBF 主色）
- 响应式布局（PC / Pad / 手机自适应）

## 🚀 本地预览

```bash
cd site
python3 -m http.server 8000
# 浏览器访问 http://localhost:8000
```

## 📦 部署到 GitHub Pages

### 方式一：自动部署（推荐）

1. Fork / 创建本仓库
2. 推送代码到 main 分支
3. 仓库 Settings → Pages
4. Source 选择 "GitHub Actions"
5. 自动触发 `.github/workflows/deploy.yml`

### 方式二：手动部署

1. 仓库 Settings → Pages
2. Source 选择 "Deploy from a branch"
3. Branch 选择 `main` / `(root)`

## 📂 目录结构

```
site/
├── index.html                # 主页面（6 区块）
├── assets/
│   ├── css/style.css         # 紫色 AI 科技风样式
│   ├── js/data.js            # 课程数据
│   ├── js/script.js          # 交互脚本
│   └── images/               # 6 张配图
├── downloads/                # 教学资料下载
│   ├── MaxKB_FDE教学讲义_小陶老师.docx
│   ├── MaxKB_FDE教学课件_小陶老师.pptx
│   ├── maxkb_core_modules.py
│   ├── README.md
│   ├── images.zip
│   └── MaxKB_FDE教学资料_v1.0.zip
├── .github/workflows/deploy.yml    # 自动部署
├── .nojekyll                        # 禁用 Jekyll
├── CNAME                            # 自定义域名（可选）
└── README.md
```

## 📞 联系

- 教师：小陶老师（陶建敏）
- 单位：广州华商学院 · 大数据专业
- 开源项目：https://github.com/1Panel-dev/MaxKB

## 📄 协议

本课程资料基于 **GPL v3** 开源，可自由用于教学。
MaxKB 项目本身基于 GPL v3 协议。

---

由 AI 小 Q 辅助设计 · 2026 年 7 月 23 日