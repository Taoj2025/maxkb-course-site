# Giscus 评论集成完整指南

> **作者**：小 Q 为小陶老师定制 · 2026-07-24 00:45
> **效果**：文章详情页（article.html）底部嵌入评论区

---

## 🎯 完成 4 步

### Step 1：开启 GitHub Discussions（您需 30 秒）

1. 打开 https://github.com/Taoj2025/maxkb-course-site/settings
2. Features 区 → 勾选 ✅ **Discussions**
3. 点击「Set up discussions」
4. 默认分类选 **General**
5. 完成

### Step 2：访问 Giscus 配置页面

打开 https://giscus.app/zh-CN

填写：
- **仓库**：`Taoj2025/maxkb-course-site`
- **Discussion 分类**：`General`
- **特性**：
  - ✅ 页面 ↔️ discussion 映射：` pathname`
  - ✅ Discussion ↔️ 评论：`specific term`（用 slug 作为 term）
- **主题**：`light`（浅色）
- **加载方式**：`lazy`（懒加载）

### Step 3：复制生成的 script 标签

Giscus 会生成一段代码，类似：

```html
<script src="https://giscus.app/client.js"
        data-repo="Taoj2025/maxkb-course-site"
        data-repo-id="R_kgDONxxx"
        data-category="General"
        data-category-id="DIC_kwDOxxx"
        data-mapping="specific"
        data-term="[ARTICLE_SLUG]"
        data-strict="1"
        data-reactions-enabled="1"
        data-emit-metadata="0"
        data-input-position="bottom"
        data-theme="light"
        data-lang="zh-CN"
        crossorigin="anonymous"
        async>
</script>
```

### Step 4：告诉我 repo-id 和 category-id

我帮您集成到 article.html。

---

## 🔧 我可以立即做的

如果您给我以下任一：
- **手动方式**：您填写 Giscus 后复制粘贴代码给我
- **自动方式**：您 GitHub PAT（能开 Discussions 权限的）

我可以：
1. 自动读取 Giscus 配置
2. 注入到 article.html
3. 测试评论功能
4. 推送 GitHub

---

*生成时间：2026-07-24 00:45 · 由 AI 小 Q 为小陶老师定制*
