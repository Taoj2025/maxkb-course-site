---
title: "Getting started with the Supabase .NET SDK"
source: "Supabase Blog"
source_url: "https://supabase.com/blog/getting-started-with-the-supabase-dotnet-sdk"
date: "2026-11-03"
auto: true
machine_summary: false
---

# 教学博客：开始使用 Supabase .NET SDK —— 面向高校学生和教师的指南

## 简介

亲爱的同学们和老师们，今天我们将一起探索如何设置和使用 Supabase 的 C# 客户端库（Supabase .NET SDK），无论是在 ASP.NET Core 项目、控制台应用程序、桌面应用、Unity 还是移动应用中。这将帮助我们在课程中更好地理解和应用现代前端部署开发（FDE）的实际案例。

## 教学场景

### 1. 课程准备

在开始之前，确保你的开发环境已经安装了以下工具：

- **.NET SDK**：建议使用最新的长期支持（LTS）版本。
- **IDE**：如 Visual Studio 或 Visual Studio Code（VS Code）。
- **Supabase 账户**：访问 [Supabase 官网](https://supabase.com/) 注册一个账户。

### 2. 课程内容

#### 步骤一：创建 Supabase 项目

1. 登录 Supabase 账户，创建一个新的项目。
2. 获取项目的 `URL` 和 `anon` 密钥，这些将在后续步骤中使用。

#### 步骤二：设置 .NET 项目

1. 打开你的 IDE，创建一个新的 .NET 项目。例如，在 VS Code 中可以使用以下命令：

   ```bash
   dotnet new console -n SupabaseDemo
   cd SupabaseDemo
   ```

2. 安装 Supabase .NET SDK：

   ```bash
   dotnet add package Supabase
   ```

#### 步骤三：编写代码

在 `Program.cs` 中添加以下代码：

```csharp
using System;
using Supabase;

class Program
{
    static async Task Main(string[] args)
    {
        // 替换为你的 Supabase URL 和 anon 密钥
        var client = new Supabase.Client("https://your-supabase-url.supabase.co", "your-anon-key");

        // 示例：获取数据
        var response = await client.From<YourTable>().Get();

        Console.WriteLine(response.Model);
    }
}
```

#### 步骤四：运行项目

在终端中运行以下命令：

```bash
dotnet run
```

### 3. 关联 MaxKB 教学

在我们的 MaxKB 课程中，学生已经学习了基本的 .NET 编程和数据库操作。通过本课程，学生可以将 Supabase 的实时数据库功能与现有的知识结合起来，进一步提升他们的全栈开发能力。

## 总结

通过本指南，学生和教师可以轻松地在各种类型的 .NET 应用中集成 Supabase，实现高效的前端部署开发。希望这能激发你们在项目中尝试更多现代工具和技术的兴趣。

---

来源：Supabase Blog

---

*本文由小Q自动抓取 + AI 重写 · 来源：[Supabase Blog](https://supabase.com/blog/getting-started-with-the-supabase-dotnet-sdk)*
