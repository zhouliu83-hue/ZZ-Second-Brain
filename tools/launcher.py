#!/usr/bin/env python3
"""一键启动器 — 把整套装置装到本机，装完就不用再想了。

用法:
    python tools/launcher.py install    # 装 hook + 定时采集
    python tools/launcher.py status     # 看当前状态
    python tools/launcher.py uninstall  # 全部卸掉

它做什么:
    1. 装 git hook（commit 前强制记日志，push 前自动体检）
    2. 装定时任务（Windows 计划任务 / macOS launchd / Linux cron）
       每 2 小时自动跑一次 capture.py，把新会话变成待审草稿
    3. 报告实际覆盖到哪些客户端，哪些采不到

它做不到什么（必须知道）:
    AI 客户端不会主动把对话推给仓库。想"连上就自动收录"，
    靠的是读客户端写在硬盘上的会话日志。
    客户端不写本地日志的（目前实测：WorkBuddy 正文不在本地库），
    就采不到——这不是脚本的问题，是客户端不给你数据。

自动化的边界:
    自动：把对话捞出来变成待审草稿、拦截没记日志的提交、自动体检
    半自动：判断哪条值得沉淀（脚本会生成草稿，但不做判断）
    纯人工：真实的客户决策内容只有你知道，AI 编不了
"""

import io
import json
import os
import platform
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
TASK_NAME = "ZZ-Second-Brain-Capture"
CRON_MARK = "# ZZ-Second-Brain-Capture"

WINDOWS_FALLBACK = """  计划任务创建被系统策略拦截（schtasks 无权限）。
  这是环境限制，不是脚本问题。两条替代路径，任选其一：

  A. 手动建一次（管理员 PowerShell，之后不会再拦）:
       schtasks /Create /F /SC HOURLY /MO 2 /TN ZZ-Second-Brain-Capture ^
         /TR "<python路径> <仓库路径>/tools/capture.py --days 3 --draft"

  B. 不装定时任务，改成手动跑（一样有效，只是要记得）:
       python tools/capture.py --days 3 --draft

  说明：git hook 不受影响，那部分照常工作。
        没有定时任务只是采集变手动，沉淀质量不打折。"""


def find_python():
    """找到可用的 python 解释器路径。"""
    for cand in (sys.executable, "python3", "python"):
        if not cand:
            continue
        try:
            subprocess.check_output(
                [cand, "--version"], stderr=subprocess.STDOUT)
            if os.path.isabs(cand):
                return cand
            out = subprocess.check_output(["which", cand]).decode().strip()
            if out:
                return out
        except (subprocess.CalledProcessError, OSError):
            continue
    return None


def run(args):
    try:
        return subprocess.run(args, capture_output=True, text=True)
    except OSError as e:
        print("执行失败：%s" % e)
        return None


def install_hooks():
    py = find_python()
    if not py:
        print("找不到 python，跳过 hook 安装")
        return False
    r = run([py, os.path.join(TOOLS, "install_hooks.py")])
    if r:
        print(r.stdout)
    return r is not None and r.returncode == 0


def install_scheduler():
    """装定时任务。返回 (成功?, 说明)。"""
    py = find_python()
    if not py:
        return False, "找不到 python"

    capture = os.path.join(TOOLS, "capture.py")
    cmd = '%s "%s" --days 3 --draft' % (py, capture)

    system = platform.system()

    if system == "Windows":
        # Windows 计划任务
        r = run(["schtasks", "/Create", "/F", "/SC", "HOURLY",
                 "/MO", "2", "/TN", TASK_NAME, "/TR", cmd])
        if r and r.returncode == 0:
            return True, "已建Windows 计划任务（每 2 小时）"
        err = r.stderr.strip() if r else "未知错误"
        if "WinError 5" in err or "拒绝访问" in err or "blacklist" in err.lower():
            return False, WINDOWS_FALLBACK
        return False, "计划任务创建失败：%s" % err

    if system == "Darwin":
        plist = os.path.expanduser(
            "~/Library/LaunchAgents/com.zzsecondbrain.capture.plist")
        content = """<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
<dict>
  <key>Label</key><string>com.zzsecondbrain.capture</string>
  <key>ProgramArguments</key>
  <array><string>%s</string><string>%s</string>
  <string>--days</string><string>3</string><string>--draft</string></array>
  <key>StartInterval</key><integer>7200</integer>
  <key>StandardOutPath</key><string>%s</string>
</dict>
</plist>
""" % (py, capture, os.path.expanduser("~/zz-capture.log"))
        try:
            with io.open(plist, "w", encoding="utf-8") as f:
                f.write(content)
            run(["launchctl", "load", "-w", plist])
            return True, "已装 launchd（每 2 小时），日志：~/zz-capture.log"
        except (IOError, OSError) as e:
            return False, "写入 plist 失败：%s" % e

    # Linux
    r = run(["crontab", "-l"])
    current = r.stdout if r and r.returncode == 0 else ""
    if CRON_MARK in current:
        return True, "cron 任务已存在"
    entry = "0 */2 * * * %s %s --days 3 --draft %s\n" % (
        py, capture, CRON_MARK)
    new = (current.rstrip("\n") + "\n" if current.strip() else "") + entry
    try:
        p = subprocess.run(["crontab", "-"], input=new,
                           capture_output=True, text=True)
        if p.returncode == 0:
            return True, "已装 cron（每 2 小时）"
        return False, "写入 crontab 失败：%s" % p.stderr.strip()
    except OSError as e:
        return False, "crontab 不可用：%s" % e


def probe_sources():
    """实测各客户端能不能采到。"""
    py = find_python()
    if not py:
        return None
    r = run([py, os.path.join(TOOLS, "capture.py"), "--days", "7"])
    return r.stdout if r else None


def status():
    py = find_python()
    print("=== 启动器状态 ===")
    print("")

    print("[git hook]")
    hooks = os.path.join(ROOT, ".git", "hooks")
    for h in ("pre-commit", "pre-push"):
        p = os.path.join(hooks, h)
        if os.path.exists(p):
            try:
                body = io.open(p, encoding="utf-8", errors="replace").read()
                mine = "沉淀守卫" in body or "闭环体检" in body
                print("  %-12s %s" % (h, "已安装（沉淀守卫）" if mine
                                       else "存在但不是本项目安装的"))
            except IOError:
                print("  %-12s 无法读取" % h)
        else:
            print("  %-12s 未安装" % h)

    print("")
    print("[定时采集]")
    system = platform.system()
    if system == "Windows":
        r = run(["schtasks", "/Query", "/TN", TASK_NAME])
        if r is None:
            print("  无法查询（schtasks 被系统策略拦截）")
            print("  可用替代：git hook 照常工作，采集改为手动跑")
            print("  python tools/capture.py --days 3 --draft")
        else:
            print("  计划任务%s" % ("已注册" if r.returncode == 0
                                     else "未注册"))
    elif system == "Darwin":
        p = os.path.expanduser(
            "~/Library/LaunchAgents/com.zzsecondbrain.capture.plist")
        print("  launchd %s" % ("已安装" if os.path.exists(p) else "未安装"))
    else:
        r = run(["crontab", "-l"])
        found = r and CRON_MARK in (r.stdout or "")
        print("  cron %s" % ("已安装" if found else "未安装"))

    print("")
    print("[各客户端可采集性]")
    out = probe_sources()
    if out:
        for line in out.splitlines():
            if line.startswith("["):
                print("  " + line.strip())
    print("")
    print("查详细健康度：python tools/evolve.py")


def uninstall():
    ok = True

    hooks = os.path.join(ROOT, ".git", "hooks")
    for h in ("pre-commit", "pre-push"):
        p = os.path.join(hooks, h)
        bak = p + ".bak"
        if os.path.exists(bak):
            try:
                body = io.open(bak, encoding="utf-8", errors="replace").read()
                if "沉淀守卫" in body or "闭环体检" in body:
                    os.remove(p)
                    print("已删除 %s" % h)
                    continue
            except IOError:
                pass
        if os.path.exists(p):
            try:
                body = io.open(p, encoding="utf-8", errors="replace").read()
                if "沉淀守卫" in body or "闭环体检" in body:
                    os.remove(p)
                    print("已删除 %s" % h)
                else:
                    print("  %s 不是本项目装的，未动" % h)
            except IOError:
                pass

    system = platform.system()
    if system == "Windows":
        r = run(["schtasks", "/Delete", "/F", "/TN", TASK_NAME])
        if r and r.returncode == 0:
            print("已删除计划任务")
    elif system == "Darwin":
        p = os.path.expanduser(
            "~/Library/LaunchAgents/com.zzsecondbrain.capture.plist")
        if os.path.exists(p):
            run(["launchctl", "unload", "-w", p])
            os.remove(p)
            print("已卸载 launchd")
    else:
        r = run(["crontab", "-l"])
        if r and r.returncode == 0 and CRON_MARK in (r.stdout or ""):
            lines = [x for x in r.stdout.splitlines()
                     if CRON_MARK not in x and x.strip()]
            p = subprocess.run(["crontab", "-"],
                               input="\n".join(lines) + "\n",
                               capture_output=True, text=True)
            if p.returncode == 0:
                print("已删除 cron 任务")

    return ok


def install():
    print("=== 安装启动器 ===\n")

    print("[1/3] git hook")
    install_hooks()

    print("[2/3] 定时采集（每 2 小时）")
    ok, msg = install_scheduler()
    print("  %s" % msg)

    print("[3/3] 探测各客户端")
    out = probe_sources()
    if out:
        for line in out.splitlines():
            if line.startswith("["):
                print("  " + line.strip())

    print("")
    print("=== 安装完成 ===")
    print("")
    print("自动的部分：")
    print("  - 新会话每 2 小时变成待审草稿到 8_contexts/inbox/")
    print("  - 改了核心规则不记日志会被 commit 拦下")
    print("  - 每次 push 前自动打印闭环体检")
    print("")
    print("仍然需要你做的：")
    print("  - 打开 8_contexts/inbox/ 里的草稿，判断哪条值得沉淀")
    print("  - 写真实客户决策到 3_behavior/decision_cases/")
    print("")
    print("为什么最后这两步不能自动化：")
    print("  判断价值需要上下文，自动提炼会把垃圾和金子一起捡进去。")
    print("  真实客户决策只有你知道，AI 编出来的会污染整个系统。")
    return 0


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "install":
        return install()
    if cmd == "uninstall":
        uninstall()
        return 0
    if cmd == "status":
        status()
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
