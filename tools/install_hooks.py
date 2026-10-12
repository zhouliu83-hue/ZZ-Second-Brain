#!/usr/bin/env python3
"""沉淀守卫 — git hook 用。在 commit 前检查该沉淀的有没有沉淀。

装法:
    python tools/install_hooks.py

装完的效果:
    每次 git commit 时自动检查。如果最近改了 0_system/ 或 1_identity/
    但没有同步更新 9_meta/system_changes.md，会拦住这次提交并说明原因。

为什么需要:
    "改了要记"这条规则，靠自觉执行了五个月，一次没执行过。
    绑定到 git commit 上，它就没地方躲。
"""

import io
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS_DIR = os.path.join(ROOT, ".git", "hooks")

HOOK_BODY = r"""#!/bin/sh
# 沉淀守卫 — 由 tools/install_hooks.py 生成
# 作用：改了核心规则却没记变更日志时，拦下这次 commit。
# 绕过方式（确实需要时）：git commit --no-verify
set -e

STAGED=$(git diff --cached --name-only)
CORE_CHANGED=$(echo "$STAGED" | grep -E '^(0_system|1_identity)/' || true)
LOGGED=$(echo "$STAGED" | grep '^9_meta/system_changes.md' || true)

if [ -n "$CORE_CHANGED" ] && [ -z "$LOGGED" ]; then
  echo ""
  echo "┌─────────────────────────────────────────────┐"
  echo "│ 改了核心规则，但没记变更日志"
  echo "└─────────────────────────────────────────────┘"
  echo "本次改动涉及:"
  echo "$CORE_CHANGED" | sed 's/^/    /'
  echo ""
  echo "三选一:"
  echo "  1. 追加一行到 9_meta/system_changes.md，再 commit"
  echo "  2. git commit --no-verify（如果你确定不需要记）"
  echo "  3. git reset（撤销这次暂存）"
  echo ""
  echo "这条规则执行了五个月一次没执行过。现在它拦在 commit 上了。"
  echo ""
  exit 1
fi
exit 0
"""

PREPUSH_BODY = r"""#!/bin/sh
# 推送前体检 — 由 tools/install_hooks.py 生成
# 作用：push 之前跑一次闭环扫描，看看沉淀区有没有长东西。
set -e

cd "$(git rev-parse --show-toplevel)"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "找不到 python，跳过体检"
  exit 0
fi

echo ""
echo "── 闭环体检 ──"
$PY tools/evolve.py 2>&1 | tail -8
echo ""
echo "注：这里只报告，不会自动 commit。判断和提炼仍需人工或 AI 完成。"
exit 0
"""


def main():
    if not os.path.isdir(HOOKS_DIR):
        print("不是 git 仓库，跳过。")
        return 0

    installed = []

    for name, body in (("pre-commit", HOOK_BODY),
                       ("pre-push", PREPUSH_BODY)):
        path = os.path.join(HOOKS_DIR, name)
        if os.path.exists(path):
            # 不覆盖已有 hook，避免破坏用户自己的设置
            backup = path + ".bak"
            with io.open(path, "r", encoding="utf-8", errors="replace") as f:
                old = f.read()
            with io.open(backup, "w", encoding="utf-8", newline="\n") as f:
                f.write(old)
            print("%s 已存在，原文件备份到 %s.bak" % (name, name))
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
        os.chmod(path, 0o755)
        installed.append(name)

    print("")
    print("已安装 hook: %s" % "、".join(installed))
    print("")
    print("效果：")
    print("  commit 前 — 改了 0_system/ 或 1_identity/ 却没记变更日志，会被拦下")
    print("  push前 — 自动跑一次闭环扫描并打印报告")
    print("")
    print("说明：hook 只存在于本地 clone，不随 git 同步。")
    print("      换机器或重新 clone 后，需要再跑一次本脚本。")
    print("      确实需要跳过时：git commit --no-verify")
    return 0


if __name__ == "__main__":
    sys.exit(main())
