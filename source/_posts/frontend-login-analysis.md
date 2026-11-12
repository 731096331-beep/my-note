---
title: 网站登录页前端代码安全性分析实验
date: 2026-11-10
categories:
  - 实验报告
tags:
  - 前端安全
  - BurpSuite
  - DVWA
  - 身份认证
permalink: frontend-login-analysis/
---

## 一、实验概述

本实验对应课程「网络嗅探与身份认证」章节的课堂小实验：**查看网站登录页面的前端代码，分析其安全性**。

很多 Web 应用把安全控制放在前端（JavaScript 校验、隐藏字段、前端跳转等），而前端代码对用户完全可见、可修改。本实验以 DVWA 靶场登录页为对象，通过「浏览器查看源代码」和「BurpSuite 拦截请求」两种手段检查前端代码，分析登录功能在实现上存在的安全问题。

<!-- more -->

## 二、实验环境

| 角色 | 系统/工具 | 说明 |
|---|---|---|
| 目标站点 | Metasploitable2 中的 DVWA | 提供登录页面 |
| 分析工具 | 浏览器（开发者工具/查看源代码） | 查看前端 HTML、JavaScript |
| 抓包工具 | Kali 自带 BurpSuite | 拦截并查看登录请求 |

## 三、实验过程

### 3.1 打开登录页面

浏览器访问 DVWA 登录页 `http://192.168.247.129/dvwa/login.php`，页面提供用户名、密码输入框和登录按钮：

{% asset_img shot1.png DVWA 登录页面 %}

### 3.2 查看前端代码

右键「查看网页源代码」（或按 F12 打开开发者工具），找到登录表单的 HTML 代码：

{% asset_img shot2.png 查看登录页前端源代码 %}

```html
<form action="login.php" method="post">
  <fieldset>
    <label for="user">Username</label>
    <input type="text" class="loginInput" size="20" name="username">
    <label for="pass">Password</label>
    <input type="password" class="loginInput" size="20" name="password">
    <input type="submit" value="Login" name="Login">
  </fieldset>
</form>
```

从代码可以读出登录功能的完整实现方式：

- 表单通过 **POST** 提交到 `login.php`，用户名、密码分别由 `username`、`password` 参数传递；
- 页面**没有任何 JavaScript 校验代码**，也没有验证码、令牌等附加控件——登录完全依赖服务端处理；
- 页面使用 **HTTP 明文协议**（地址栏无 HTTPS），提交的数据未加密。

### 3.3 用 BurpSuite 拦截登录请求

为验证「前端代码反映的传输方式是否属实」，用 BurpSuite 的 Proxy 功能捕获一次真实登录请求。配置浏览器代理指向 BurpSuite（127.0.0.1:8080），在登录页输入账号密码点击 Login，在 BurpSuite 的 Proxy 中查看捕获到的请求与响应（Intercept 拦截或 HTTP history 记录）：

{% asset_img shot3.png BurpSuite 捕获到的登录请求 %}

POST 请求体中，用户名、密码以**明文**形式原样传输：

```http
POST /dvwa/login.php HTTP/1.1
Host: 192.168.247.129
...

username=admin&password=password&Login=Login
```

这与前端代码的分析结果一致：登录凭证没有经过任何加密或编码处理。响应头还暴露了服务器版本信息（`Server: Apache/2.2.8`、`X-Powered-By: PHP/5.2.4`）。

## 四、安全性分析

结合前端代码与抓包结果，该登录页存在以下安全问题：

1. **凭证明文传输**：登录使用 HTTP，用户名密码在网络上明文传输。结合课程「网络嗅探」章节可知，同网段攻击者用 Wireshark 等工具即可直接嗅探到账号密码；公网环境下中间人攻击同样可行。应改为 HTTPS（TLS）加密传输。

2. **前端无任何校验与防护**：没有验证码、登录失败锁定、频率限制等机制。结合 BurpSuite 的 Intruder 功能，攻击者可以方便地对登录接口进行暴力猜解、字典攻击。

3. **前端代码完全透明**：前端代码任何人都能查看，参数名（`username`、`password`）、提交路径（`login.php`）暴露无遗，为攻击者构造请求提供了便利。安全控制如果放在前端（如本课所讲的滑块验证只在前端校验），可以直接被绕过——BurpSuite 拦截后篡改参数再放行即可。

4. **无 CSRF 防护**：登录表单没有一次性令牌（token），存在跨站请求伪造的隐患。

5. **服务器指纹信息泄露**：响应头直接暴露 `Apache/2.2.8` 与 `PHP/5.2.4` 等版本信息，两者都是已停止维护多年的老版本，攻击者无需猜测即可按版本选择对应的漏洞利用代码。应隐藏或伪造版本头（如 `ServerTokens Prod`），并及时升级 Web 服务组件。

## 五、加固建议

- 全站启用 HTTPS，登录凭证必须经 TLS 加密传输；
- 关键安全校验放在服务端，前端校验只用于提升用户体验，不能作为安全控制；
- 增加验证码、登录失败锁定、尝试频率限制等防暴力破解措施；
- 为表单加入随机 CSRF Token 并做服务端校验；
- 登录错误提示保持统一（如「用户名或密码错误」），避免泄露用户是否存在。

## 六、总结

本次实验通过查看前端代码与 BurpSuite 抓包，分析了 DVWA 登录页的安全性。体会是：**前端代码是攻击者了解目标的第一手资料**——表单结构、参数名、校验逻辑全部公开可见；而前端能做的任何「安全校验」都可以被篡改绕过。因此登录等关键安全机制必须由服务端实现，并配合加密传输与防爆破手段，才能形成有效的认证防线。
