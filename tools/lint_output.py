#!/usr/bin/env python3
"""输出质量机检 — 只检查 0_system/quality_control.md 里可机器判定的部分。

用法:
    python tools/lint_output.py <文件路径>
    python tools/lint_output.py -            # 从stdin 读取

设计约束（重要）:
    只检查形式层：禁用词、句长、段长、字数区间、空结构。
    不检查内容质量。洞察、锐度、共鸣这些东西没有确定性阈值，
    硬判只会让人学会"为了过检而写"。

退出码恒为 0。本脚本只报告，不阻断。
"""

import re
import sys
import io

# ---- 来自 0_system/anti_generic_rules.md 的语言层禁令 ----
BANNED_PHRASES = [
    "在当今这个快速变化的时代",
    "在快速变化的时代",
    "从某种程度上说",
    "从某种角度",
    "值得注意的是",
    "不可否认",
    "总的来说",
    "综上所述",
    "我们需要认识到",
    "这是一个复杂的问题",
    "赋能",
    "抓手",
    "闭环",
    "底层逻辑",
    "正能量",
]

# ---- 来自 0_system/quality_control.md 的禁忌检查 ----
BANNED_CTA = [
    "评论区告诉我",
    "评论区见",
    "双击屏幕",
    "点赞收藏转发",
    "主页简介",
    "私信我",
    "加V",
    "加微信",
    "关注我",
]

# ---- 来自 1_identity/identity.md 的固定结尾 ----
FIXED_ENDING = "我是周正，你素未谋面的朋友，从贵州走出去的创业者，主页置顶的是我送你的一份礼物。"

# ---- 阈值：来自 0_system/output_rules.md ----
MAX_SENTENCE_LEN = 30
MAX_PARAGRAPH_LEN = 80
HOOK_INTERVAL = 150


def split_sentences(text):
    """按中文标点切句，保留标点。"""
    parts = re.split(r"([。！？!?；;])", text)
    out = []
    buf = ""
    for p in parts:
        if not p:
            continue
        buf += p
        if p in "。！？!?；;":
            s = buf.strip()
            if len(s) > 1:
                out.append(s)
            buf = ""
    if buf.strip():
        out.append(buf.strip())
    return out


def load_text(path):
    if path == "-":
        return sys.stdin.read()
    with io.open(path, "r", encoding="utf-8") as f:
        return f.read()


def lint(text):
    problems = []   # (等级, 说明)
    stats = {}

    body = text.strip()
    if not body:
        return stats, [("!", "内容为空")]

    paras = [p.strip() for p in body.split("\n") if p.strip()]
    stats["字数"] = len(re.sub(r"\s", "", body))
    stats["段落数"] = len(paras)

    # 1. 禁用空词
    hits = []
    for phrase in BANNED_PHRASES:
        n = body.count(phrase)
        if n:
            hits.append("%s×%d" % (phrase, n))
    if hits:
        problems.append(("!", "命中禁用空词：" + "、".join(hits)))

    # 2. 引导互动 / 硬广
    cta = [p for p in BANNED_CTA if p in body]
    if cta:
        problems.append(("!", "出现引导互动或硬广话术：" + "、".join(cta)))

    # 3. 句长（固定人设句豁免——它必须一字不改，天然超长）
    sentences = split_sentences(body)
    sentences = [s for s in sentences if FIXED_ENDING not in s]
    long_sent = [s for s in sentences if len(s) > MAX_SENTENCE_LEN]
    stats["超长句"] = len(long_sent)
    if long_sent:
        problems.append((
            "~",
            "有 %d 句超过 %d 字，最长 %d 字：%s"
            % (len(long_sent), MAX_SENTENCE_LEN,
               max(len(s) for s in long_sent), long_sent[0][:30]),
        ))

    # 4. 段长
    long_para = [p for p in paras if len(p) > MAX_PARAGRAPH_LEN]
    stats["超长段"] = len(long_para)
    if long_para:
        problems.append((
            "~",
            "有 %d 段超过 %d 字" % (len(long_para), MAX_PARAGRAPH_LEN),
        ))

    # 5. 钩子密度（每150 字一个）
    n_chars = stats["字数"]
    expected = max(1, n_chars // HOOK_INTERVAL)
    stats["应埋钩子"] = expected

    # 6. 人设回收
    has_ending = FIXED_ENDING in body
    stats["人设回收"] = "有" if has_ending else "无"
    if not has_ending:
        problems.append((
            "~",
            "结尾没有固定人设句。若是短视频文案，按 identity.md 补上。",
        ))

    return stats, problems


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    try:
        text = load_text(sys.argv[1])
    except IOError as e:
        print("读取失败：%s" % e)
        return 0

    stats, problems = lint(text)

    print("=== 机检报告 ===")
    for k in sorted(stats):
        print("  %-8s %s" % (k, stats[k]))
    print()

    if not problems:
        print("形式层通过。内容质量需人工判断。")
        return 0

    for level, msg in problems:
        print("[%s] %s" % (level, msg))

    print()
    hard = [p for p in problems if p[0] == "!"]
    if hard:
        print("必改 %d 项，建议改 %d 项。"
              % (len(hard), len(problems) - len(hard)))
    else:
        print("无必改项，建议改 %d 项。" % (len(problems) - len(hard)))
    print("提醒：过了机检不等于内容好。洞察和锐度这里判不了。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
