#!/usr/bin/env python3
"""进化闭环健康扫描 — 检查 evolution_protocol.md 六步闭环的沉淀区是否在长东西。

用法:
    python tools/evolve.py           # 扫描并报告
    python tools/evolve.py --write   # 扫描并更新 9_meta/evolution_state.json

退出码恒为 0。只报告，不阻断。
"""

import io
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "9_meta", "evolution_state.json")

# 六步闭环里需要沉淀的目录。key 是闭环环节，value 是目录。
CLOSURE = [
    ("3_output", [
        ("7_ai_training/high_quality_examples", "优质输出样本"),
        ("7_ai_training/bad_examples", "劣质输出样本"),
    ]),
    ("4_feedback", [
        ("7_ai_training/benchmark_outputs", "基准实测记录"),
        ("7_ai_training/corrected_outputs", "修正记录"),
        ("7_ai_training/style_alignment", "风格对齐记录"),
    ]),
    ("5_extract", [
        ("6_memory/insights", "洞察"),
        ("6_memory/failures", "失败经验"),
        ("6_memory/breakthroughs", "突破记录"),
        ("6_memory/experiments", "实验记录"),
        ("6_memory/observations", "观察"),
    ]),
    ("6_update", [
        ("3_behavior/decision_cases", "决策轨迹"),
        ("6_memory/projects", "项目记录"),
    ]),
]

# 文件名里带这些词的视为模板，不算实际内容。
TEMPLATE_HINTS = ["template", "模板", "index", "readme", "指南", "说明"]
INDEX_FILES = {"index.md", "README.md"}


def is_template(fname):
    low = fname.lower()
    return any(h in low for h in TEMPLATE_HINTS) or fname in INDEX_FILES


def scan_dir(path):
    """返回 (实际内容文件数, 模板文件数, 字符数)。"""
    full = os.path.join(ROOT, path)
    if not os.path.isdir(full):
        return (0, 0, 0, "目录不存在")
    real, tpl, chars = 0, 0, 0
    for f in os.listdir(full):
        fp = os.path.join(full, f)
        if not os.path.isfile(fp):
            continue
        if f.startswith("."):
            continue
        if not f.endswith(".md"):
            continue
        if is_template(f):
            tpl += 1
            continue
        real += 1
        try:
            with io.open(fp, "r", encoding="utf-8") as fh:
                chars += len(fh.read())
        except (IOError, UnicodeDecodeError):
            pass
    return (real, tpl, chars, "")


def read_state():
    if not os.path.isfile(STATE):
        return None
    try:
        with io.open(STATE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (IOError, ValueError, UnicodeDecodeError):
        return None


def main():
    write = "--write" in sys.argv
    prev = read_state()

    lines = []
    total_real = 0
    total_chars = 0
    ring = []

    for stage, dirs in CLOSURE:
        lines.append("")
        lines.append("[%s]" % stage)
        for path, label in dirs:
            real, tpl, chars, err = scan_dir(path)
            total_real += real
            total_chars += chars
            ring.append((stage, path, real, chars))
            if err:
                lines.append("  %-42s %s" % (label, err))
            elif real == 0:
                lines.append("  %-42s 空（%d 个模板）" % (label, tpl))
            else:
                lines.append("  %-42s %d 份 / %d 字符"
                             % (label, real, chars))

    lines.insert(0, "=== 进化闭环沉淀区扫描 ===")

    # 环比
    lines.append("")
    if prev:
        old_map = {}
        for item in prev.get("inventory", []):
            old_map[item["path"]] = item["real"]
        grew, same = [], []
        for stage, path, real, chars in ring:
            o = old_map.get(path)
            if o is None:
                continue
            if real > o:
                grew.append("%s (+%d)" % (path, real - o))
            elif real < o:
                grew.append("%s (%d)" % (path, real - o))
            else:
                same.append(path)
        if grew:
            lines.append("环比变化: " + "、".join(grew))
        else:
            lines.append("环比变化: 无新增。上次扫描至今 %d 个目录零变化。"
                         % len(same))
    else:
        lines.append("环比变化: 首次扫描，已建立基线。")

    lines.append("")
    lines.append("总计: %d 份实际内容 / %d 字符" % (total_real, total_chars))
    lines.append("")
    lines.append("判读: 前两环（输入/分析）不需要沉淀，看后面四环有没有东西。")
    if total_real == 0:
        lines.append("当前状态: 闭环第 3 环为空。这是系统不進化的根本原因。")

    report = "\n".join(lines)
    print(report)

    if write:
        data = {
            "updated": time.strftime("%Y-%m-%d"),
            "total_real_files": total_real,
            "total_chars": total_chars,
            "inventory": [
                {"stage": s, "path": p, "real": r, "chars": c}
                for s, p, r, c in ring
            ],
        }
        with io.open(STATE, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
            f.write("\n")
        print("")
        print("已更新 9_meta/evolution_state.json")
    else:
        print("")
        print("加 --write 可把本次结果写入 9_meta/evolution_state.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
