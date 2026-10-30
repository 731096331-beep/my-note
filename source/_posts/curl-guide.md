---
title: curl 命令行工具入门实践
date: 2026-10-27
categories:
  - 学习笔记
tags:
  - curl
  - 命令行
  - HTTP
permalink: curl-guide/
---

## 一、curl 是什么

curl（Client URL）是一款功能强大的命令行工具，用于在客户端与服务器之间传输数据。它支持 HTTP、HTTPS、FTP、SFTP 等 20 多种协议，无需浏览器就能完成发请求、下载文件、调试接口等操作，是开发者进行 API 调试、网络问题排查和自动化脚本编写的核心工具。

<!-- more -->

它的优点在于：

- **跨平台**：Windows、Linux、macOS 均自带或易于安装；
- **轻量**：不渲染页面，直接展示原始请求与响应数据；
- **参数丰富**：通过参数即可控制请求方法、请求头、超时、重定向等；
- **可脚本化**：输出结果可以和其他命令（管道、重定向）组合使用。

## 二、常用场景实践

本次实践在 Windows 的 Git Bash 终端中进行，演示了 curl 最常用的几个场景。

**1. 查看版本与支持的协议**

```bash
curl --version
```

第一步先确认 curl 已正确安装，并查看其版本号与支持的协议列表。

{% asset_img shot1.png curl --version 查看版本信息与支持的协议 %}

**2. 发起 GET 请求获取数据**

```bash
curl https://api.github.com/users/731096331-beep
```

直接跟一个 URL，curl 默认发起 GET 请求并输出响应内容。这里请求 GitHub 的开放 API，返回一段 JSON 格式的用户信息——这正是 API 调试的典型场景：在命令行里直接查看接口的原始返回。

{% asset_img shot2.png curl 请求 GitHub API 返回 JSON 数据 %}

**3. 只看响应头**

```bash
curl -I https://731096331-beep.github.io/my-note/
```

`-I`（HEAD 请求）只返回 HTTP 响应头，不下载页面正文。响应头中包含状态码（200）、服务器类型（GitHub Pages）、缓存策略等信息，是排查网站是否正常响应的快捷手段。

{% asset_img shot3.png curl -I 只查看 HTTP 响应头 %}

**4. 下载并保存文件**

```bash
curl -o mynote.html https://731096331-beep.github.io/my-note/
```

`-o` 指定保存的文件名，把网页内容下载到本地。再用 `ls` 确认文件已生成，可以看到文件大小与网页体积一致。

{% asset_img shot4.png curl -o 下载网页并用 ls 确认文件生成 %}

**5. 查看完整通信过程**

```bash
curl -v https://api.github.com/users/731096331-beep
```

`-v`（verbose）展示请求的完整过程：包括 DNS 解析、TLS 握手、发出的请求头（`>` 开头）与收到的响应头（`<` 开头）。这是排查网络问题（如证书错误、超时、重定向）时最有用的一个参数。

{% asset_img shot5.png curl -v 查看完整通信过程 %}

## 三、常用参数速查

| 参数 | 作用 | 示例 |
|---|---|---|
| `-o 文件名` | 将响应保存到指定文件 | `curl -o page.html URL` |
| `-I` | 只请求响应头（HEAD） | `curl -I URL` |
| `-v` | 显示完整通信过程 | `curl -v URL` |
| `-L` | 自动跟随重定向 | `curl -L URL` |
| `-A "UA"` | 自定义 User-Agent | `curl -A "MyTool/1.0" URL` |
| `-X 方法` | 指定请求方法（GET/POST 等） | `curl -X POST URL` |
| `-d "数据"` | 发送 POST 表单数据 | `curl -d "a=1" URL` |
| `-H "头: 值"` | 自定义请求头 | `curl -H "Content-Type: application/json" URL` |
| `-s` | 静默模式，不显示进度 | `curl -s URL` |

## 四、小结

通过本次实践，掌握了 curl 的基本用法：查看版本信息、发起 GET 请求获取接口数据、只查看响应头、下载保存文件，以及用 `-v` 观察完整的 HTTP 通信过程。curl 把「请求-响应」的过程完全暴露在命令行里，比浏览器更直观地展示了 HTTP 协议的工作方式。后续学习 Web 安全（如 SQL 注入、目录扫描的手工验证）时，curl 也将是随时会用到的基础工具。
