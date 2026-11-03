---
title: "Introducing the unified Supabase .NET SDK"
source: "Supabase Blog"
source_url: "https://supabase.com/blog/introducing-the-unified-supabase-net-sdk"
date: "2026-11-03"
auto: true
machine_summary: false
---

# 统一 Supabase .NET SDK 教学指南

亲爱的同学们和老师们，

今天我们来聊聊一个让前端部署开发（**FDE**）变得更加简便的工具——**Supabase .NET SDK**。最近，Supabase 团队宣布将他们的 .NET 库整合到一个统一的代码库中，并且采用统一的版本号。这对于我们教学和学生学习来说，是一个非常好的消息。

## 为什么统一很重要？

在教学过程中，我们常常会遇到学生因为不同版本的库而遇到各种兼容性问题。统一的 SDK 可以帮助我们减少这些困扰，让学生在学习过程中更加专注于实际开发，而不是花费大量时间在版本兼容和依赖管理上。

### 教学场景示例

假设我们在 **MaxKB FDE 培训** 中教授一个关于实时数据库的项目。以往，学生可能需要分别学习和管理多个 Supabase 的 .NET 库，比如身份验证、数据库访问等。现在，通过统一的 SDK，学生可以更快速地上手：

1. **安装统一 SDK**：只需一个包，学生可以通过 NuGet 包管理器轻松安装。
   ```bash
   Install-Package Supabase
   ```
2. **统一 API 调用**：学生可以更方便地调用各种 Supabase 服务，因为所有功能都集中在一个包中。
   ```csharp
   var client = new Supabase.Client("your-anon-key");
   var auth = client.Auth;
   var db = client.DB;
   ```
3. **简化项目配置**：统一的配置方式让学生更容易理解和维护项目结构。

## 如何在教学中使用？

作为教师，我们可以在课程设计中加入以下内容：

- **基础入门**：介绍 Supabase 和 .NET SDK 的基本概念和使用场景。
- **实战演练**：设计一个小型项目，让学生在实践中掌握 SDK 的使用。
- **案例分析**：分析一些使用 Supabase 的实际案例，帮助学生理解其应用场景和优势。

## 关联 MaxKB 教学

在 **MaxKB FDE 培训** 中，我们可以将 Supabase .NET SDK 的学习与前端框架（如 React 或 Vue）的教学结合起来，帮助学生构建完整的前后端解决方案。

希望这篇指南能帮助大家更好地理解和使用 Supabase .NET SDK。如果有任何问题或建议，欢迎在课堂上与我讨论！

来源：Supabase Blog

---

*本文由小Q自动抓取 + AI 重写 · 来源：[Supabase Blog](https://supabase.com/blog/introducing-the-unified-supabase-net-sdk)*
