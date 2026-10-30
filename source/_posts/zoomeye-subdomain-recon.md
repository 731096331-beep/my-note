---
title: 空间搜索引擎对比（ZoomEye 类平台）与子域名收集实践
date: 2026-10-20
categories:
  - 学习笔记
tags:
  - ZoomEye
  - 空间搜索引擎
  - 子域名收集
  - 信息收集
permalink: zoomeye-subdomain-recon/
---

## 一、与 ZoomEye 功能类似的空间搜索引擎

空间搜索引擎（Cyberspace Search Engine）是指对全网设备、开放端口、服务指纹进行主动测绘，并将结果建立可检索索引的平台。ZoomEye（知道创宇出品）是其中之一，与其功能类似的主流平台还有：

<!-- more -->

| 平台 | 开发方 | 特色 | 访问地址 |
|---|---|---|---|
| Shodan | 美国（John Matherly） | 最早的设备搜索引擎，banner 指纹库庞大，可关联 CVE 编号与漏洞利用提示，数据偏向全球 | shodan.io |
| FOFA | 华顺信安（白帽汇） | 国内使用最广，搜索语句灵活（title=、body=、icon_hash= 等），资产测绘与关联分析能力强 | fofa.info |
| Censys | 美国密歇根大学背景 | 学术出身，数据基于证书透明日志与全网扫描，主机与证书数据质量高 | censys.io |
| Quake | 360 | 资产测绘 + 漏洞线索关联，界面对新手友好 | quake.360.net |
| Hunter（鹰图） | 奇安信 | 图标搜索（icon hash）定位同类资产、关联域名发现，适合攻防演练目标梳理 | hunter.qianxin.com |
| BinaryEdge | 瑞士 | 采集 40 余种数据类型（端口、证书、漏洞、种子/物联网等） | binaryedge.io |
| GreyNoise | 美国 | 专门区分「全网扫描噪音」与「定向扫描」，帮助研判告警是否值得响应 | greynoise.io |

各平台共同点：都是**被动测绘**——只记录公网暴露的设备与服务信息，不主动入侵；差异主要在数据覆盖范围（国内资产 FOFA/ZoomEye/Hunter 更全）、语法灵活度与免费额度。

## 二、结合 ZoomEye 进行相关搜索

**操作步骤：**

1. 注册并登录 ZoomEye（国际站 zoomeye.org，国内站 zoomeye.hq，二者账号通用、数据基本一致）。
2. 在搜索框输入检索语句，常用语法示例：

```
app:"GitLab"                      # 搜索特定 Web 应用
service:http country:"CN"         # 中国地区的 HTTP 服务
port:3306 os:"Linux"              # 运行 Linux 且开放 3306 端口的设备
ip:"目标IP"                        # 查看某 IP 的暴露面
city:"Guilin" service:ssh         # 按城市 + 服务检索
```

3. 观察搜索结果列表：每条结果包含 IP、开放端口、服务类型、banner 指纹、地理位置等信息。

{% asset_img shot1.png ZoomEye 搜索结果列表 %}
4. 点击某条结果进入**资产详情页**，查看该主机的完整暴露面（端口列表、服务版本、HTTP 响应头等）。

{% asset_img shot2.png ZoomEye 资产详情页：主机的完整暴露面 %}
5. 使用**统计视图**查看搜索结果的按国家、按服务类型的分布情况。

{% asset_img shot3.png ZoomEye 统计视图：按国家、服务类型分布 %}

## 三、子域名收集

子域名收集是信息收集中最基础的环节：子域名往往是防护薄弱的入口（测试环境、老旧系统、管理后台常挂在子域名上）。常用方法按「被动优先、主动补充」的顺序如下：

**1. 证书透明日志（被动，最推荐）**

访问 crt.sh，输入主域名（如 example.com）即可查询该域名历史上所有签发过 HTTPS 证书的子域名，无需登录、不产生扫描流量。

{% asset_img shot4.png crt.sh 证书透明日志查询结果 %}

**2. 搜索引擎语法（被动）**

- 传统搜索引擎：`site:example.com`
- 空间搜索引擎：FOFA 中 `domain="example.com"`，ZoomEye 中 `site:example.com`

{% asset_img shot5.png 搜索引擎语法检索子域名结果 %}

**3. 子域名收集工具**

本次实践采用**在线工具**——DNSdumpster（https://dnsdumpster.com）。无需本地安装，在页面输入目标域名并验证后，即可自动汇总该域名的子域名、DNS 记录（A / MX / TXT 等）与主机地理分布：

{% asset_img shot6.png DNSdumpster 在线查询结果（一） %}
{% asset_img shot7.png DNSdumpster 在线查询结果（二） %}

若在本地环境操作，也可以选择命令行工具方案：subfinder 是被动聚合类工具的代表，一条命令即可从多个公开数据源（证书日志、DNS 记录库等）汇总子域名：

```bash
subfinder -d example.com -o subdomains.txt
```

同类工具还有 OneForAll（国内常用）、amass 等；纯字典爆破（layer、ksubdomain）属于主动方式，速度慢且易触发告警，一般放到最后。

**4. 结果整理**

- 去重、排序；
- 对收集到的子域名批量解析 IP（dig / nslookup / 脚本）；
- 存活探测（如 httpx -l subdomains.txt），确认哪些子域名对外提供服务。

## 四、合规提示

- 以上所有操作均为**被动信息收集**，利用的是公开数据，未涉及任何入侵行为；
- 实践时应选择**自己有权限的目标**（如自己学校的域名、授权的靶场域名），不要对无授权的第三方域名做批量探测；
- 作业中展示的截图注意对无关 IP、账号信息做脱敏处理。

## 五、总结

本次作业对比了 ZoomEye 与 Shodan、FOFA、Censys、Quake、Hunter 等空间搜索引擎的定位与特点，实践了使用 ZoomEye 检索公网资产，并通过证书透明日志、搜索引擎语法与在线工具 DNSdumpster 完成了子域名收集。体会是：现代互联网的「暴露面」远比想象中大，攻击者能轻易获取的信息远超普通人的直觉——这也正是资产测绘与子域名梳理作为安全运维日常工作的意义。
