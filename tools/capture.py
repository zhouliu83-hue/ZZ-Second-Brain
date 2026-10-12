#!/usr/bin/env python3
"""会话采集器 — 从 AI 客户端的本地日志里捞出对话，喂给沉淀流程。

用法:
    python tools/capture.py              # 扫描各客户端，列出待处理会话
    python tools/capture.py --draft      # 生成待审草稿到 8_contexts/inbox/
    python tools/capture.py --days 7# 只看最近 7 天
    python tools/capture.py --source claude

为什么需要这个:
    AI 客户端不会把对话推给GitHub。想"连上就自动收录"，
    唯一可行的办法是读客户端写在本地硬盘上的会话日志。

它做什么:
    扫描 → 找到未处理的会话 → 提取用户消息 + AI 回复摘要 → 生成草稿
它不做什么:
    不判断哪条值得沉淀（那是人的事，或者让 AI 读草稿后自己挑）
    不自动 push
    不碰任何 AI 客户端的数据（只读）

数据只读:
    本脚本对客户端日志只做读取，不写入、不删除、不修改。
"""

import argparse
import hashlib
import io
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta

HOME = os.path.expanduser("~")

# ---- 客户端日志源 ----
# 每种客户端的会话日志位置和解析方式不同。
# 新增客户端只需在这里加一项，不用改其他代码。
SOURCES = {
    "claude": {
        "label": "Claude Code",
        "pattern": os.path.join(HOME, ".claude", "projects", "**", "*.jsonl"),
        "parser": "claude_jsonl",
        "works": True,
    },
    "codex": {
        "label": "Codex",
        "pattern": os.path.join(HOME, ".codex", "sessions", "**", "*.jsonl"),
        "parser": "claude_jsonl",   # 结构相近，失败时会被跳过
        "works": "unknown",
    },
    "workbuddy": {
        "label": "WorkBuddy",
        "pattern": os.path.join(HOME, ".workbuddy", "sessions", "*.json"),
        "parser": "workbuddy_meta",
        "works": False,   # 只有元数据，没有正文
    },
}

INBOX = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "8_contexts", "inbox")


def find_files(pattern):
    import glob
    return glob.glob(pattern, recursive=True)


# ---- Claude Code / Codex jsonl 解析 ----
def parse_claude_jsonl(path):
    """从 jsonl 提取用户提问和 AI 回复。返回 dict 或 None。"""
    turns = []
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue

                t = d.get("type")
                if t not in ("user", "assistant"):
                    continue
                msg = d.get("message") or {}
                content = msg.get("content")

                texts = []
                if isinstance(content, str):
                    texts = [content]
                elif isinstance(content, list):
                    for part in content:
                        if not isinstance(part, dict):
                            continue
                        if part.get("type") == "text":
                            texts.append(part.get("text", ""))

                text = "\n".join(x for x in texts if x).strip()
                if not text:
                    continue

                # 过滤掉纯工具调用和系统注入
                if text.startswith("<") and "system-reminder" in text[:200]:
                    continue
                if len(text) < 10:
                    continue

                turns.append({
                    "role": t,
                    "text": text,
                    "ts": d.get("timestamp"),
                })
    except (IOError, OSError):
        return None

    if not turns:
        return None

    first_ts = next((x["ts"] for x in turns if x["ts"]), None)
    dt = None
    if first_ts:
        try:
            dt = datetime.strptime(first_ts[:19], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            dt = None

    return {
        "source": "claude",
        "path": path,
        "turns": turns,
        "dt": dt,
        "n_turns": len(turns),
        "sig": hashlib.md5(path.encode("utf-8")).hexdigest()[:8]
               + str(len(turns)),
    }


# ---- WorkBuddy 解析（只有元数据）----
def parse_workbuddy_meta(path):
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
    except (IOError, ValueError, UnicodeDecodeError):
        return None

    if not isinstance(d, dict) or "sessionId" not in d:
        return None

    started = d.get("startedAt")
    dt = None
    if isinstance(started, (int, float)):
        try:
            dt = datetime.fromtimestamp(started / 1000)
        except (ValueError, OSError):
            dt = None

    return {
        "source": "workbuddy",
        "path": path,
        "turns": [],
        "dt": dt,
        "n_turns": 0,
        "meta_only": True,
        "cwd": d.get("cwd", ""),
        "sig": hashlib.md5(path.encode("utf-8")).hexdigest()[:8],
    }


PARSERS = {
    "claude_jsonl": parse_claude_jsonl,
    "workbuddy_meta": parse_workbuddy_meta,
}


def already_drafted(sig):
    """检查这个会话是否已经生成过草稿。"""
    if not os.path.isdir(INBOX):
        return False
    for f in os.listdir(INBOX):
        if f.endswith(".md") and sig in f:
            return True
    return False


def summarize_session(sess, max_turn=6):
    """提取用户提问（这是判断价值的关键）。"""
    users = [t["text"] for t in sess["turns"] if t["role"] == "user"]
    assistants = [t["text"] for t in sess["turns"] if t["role"] == "assistant"]
    return users[-max_turn:], assistants[-2:]


def clean(text, limit=600):
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    if len(text) > limit:
        text = text[:limit] + "…"
    return text


def make_draft(sess):
    users, assistants = summarize_session(sess)
    dt = sess.get("dt") or datetime.now()
    date = dt.strftime("%Y-%m-%d")
    src = SOURCES[sess["source"]]["label"]

    lines = []
    lines.append("---")
    lines.append("name: inbox-%s-%s" % (date, sess["sig"]))
    lines.append("description: 从%s自动采集的未整理会话。待人工/AI 判断是否值得沉淀。" % src)
    lines.append("type: inbox")
    lines.append("importance: low")
    lines.append("source: %s" % src)
    lines.append("session_sig: %s" % sess["sig"])
    lines.append("date: %s" % date)
    lines.append("---")
    lines.append("")
    lines.append("# 待整理会话：%s（%s）" % (date, src))
    lines.append("")
    lines.append("> 本文件由 `tools/capture.py` 自动生成，**内容未经过滤**。")
    lines.append("> 处理方式：读完下面三问，有一条答\"是\"就提炼进对应目录，然后删掉本文件。")
    lines.append(">")
    lines.append("> 1. 这里面有没有一个**真实的决策**（我做了什么选择、被否了什么、结果如何）？")
    lines.append("> 2. 有没有一条 **AI 说错了、我纠正了**的地方？")
    lines.append("> 3. 有没有一个**当时以为对、后来被验证是错的**判断？")
    lines.append("")
    lines.append("三条都是\"否\" → 直接删掉本文件，不用留。")
    lines.append("")
    lines.append("## 会话元信息")
    lines.append("")
    lines.append("- 采集时间：%s" % dt.strftime("%Y-%m-%d %H:%M"))
    lines.append("- 来源：%s" % src)
    lines.append("- 轮次数：%d" % sess["n_turns"])
    lines.append("")

    if users:
        lines.append("## 我问的（最近 %d 条）" % len(users))
        lines.append("")
        for i, u in enumerate(users, 1):
            lines.append("**Q%d**" % i)
            lines.append("")
            lines.append("> " + clean(u, 500).replace("\n", "\n> "))
            lines.append("")

    if assistants:
        lines.append("## AI 回的（最近 %d 条摘要）" % len(assistants))
        lines.append("")
        for i, a in enumerate(assistants, 1):
            lines.append("**A%d**" % i)
            lines.append("")
            lines.append("> " + clean(a, 400).replace("\n", "\n> "))
            lines.append("")

    return "\n".join(lines) + "\n", date


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", action="store_true",
                    help="生成待审草稿到 8_contexts/inbox/")
    ap.add_argument("--days", type=int, default=14,
                    help="只看最近 N 天的会话，默认 14")
    ap.add_argument("--source", default=None,
                    help="只处理指定客户端（claude/codex/workbuddy）")
    args = ap.parse_args()

    cutoff = datetime.now() - timedelta(days=args.days)
    keys = [args.source] if args.source else list(SOURCES)

    print("=== 会话采集 ===")
    print("扫描最近 %d 天\n" % args.days)

    drafted = 0
    skipped = 0

    for key in keys:
        src = SOURCES.get(key)
        if not src:
            print("未知来源：%s" % key)
            continue

        files = find_files(src["pattern"])
        if not files:
            print("[%s] 没找到日志文件" % src["label"])
            if src["works"] is False:
                print("       该客户端本地只存元数据，对话正文不在硬盘上，")
                print("       无法自动采集。需要在客户端里手动保存。")
            print()
            continue

        got = 0
        for path in files:
            sess = PARSERS[src["parser"]](path)
            if not sess:
                skipped += 1
                continue
            if sess.get("dt") and sess["dt"] < cutoff:
                continue
            if sess.get("meta_only"):
                continue
            got += 1

            if already_drafted(sess["sig"]):
                continue

            if args.draft:
                if not os.path.isdir(INBOX):
                    os.makedirs(INBOX)
                content, date = make_draft(sess)
                name = "%s_%s_%s.md" % (date, key, sess["sig"])
                with io.open(os.path.join(INBOX, name), "w",
                             encoding="utf-8") as f:
                    f.write(content)
                drafted += 1
                print("[%s] 已生成草稿：%s" % (src["label"], name))
            else:
                print("[%s] %d 轮  %s  %s"
                      % (src["label"], sess["n_turns"],
                         sess.get("dt").strftime("%Y-%m-%d") if sess.get("dt") else "无时间",
                         os.path.basename(path)[:20]))

        if got == 0 and src["works"] is False:
            print("[%s] 只找到元数据，无正文可采" % src["label"])
        print()

    if args.draft:
        print("生成 %d 份草稿到 8_contexts/inbox/" % drafted)
        if drafted:
            print("")
            print("下一步：让 AI 读这些草稿，按开头三问决定提炼还是删除。")
            print("这是唯一需要人/AI 参与的一步——自动判断价值不可靠。")
    else:
        print("加 --draft 可生成待审草稿。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
