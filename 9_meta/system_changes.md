---
name: system_changes
description: 系统重要变更记录。
type: meta
importance: medium
last_updated: 2026-10-12
---

# 系统变更

## 变更记录格式

```
YYYY-MM-DD | 文件 | 变更类型 | 变更说明
```

## 记录

2026-05-10 | 全部模块 | init | 系统初始化，10 模块 61 文件填充
2026-05-10 | 6_memory/ | add | 3 条洞察 + 1 条观察 + 3 份会话
2026-10-12 | tools/lint_output.py | add | 新增。机检脚本，把 quality_control 可判定部分变成命令
2026-10-12 | tools/evolve.py | add | 新增。闭环扫描脚本，六环节产出可量化、可环比
2026-10-12 | tools/README.md | add | 新增。脚本设计原则
2026-10-12 | 7_ai_training/benchmark_outputs/2026-10-12_benchmark_v1.md | add | 新增。三道固定题 + 打分表。基准 C（立场层）权重最高
2026-10-12 | 3_behavior/decision_cases/2026-05-10_多AI共享同一仓库的协作策略.md | add | 新增。首条决策轨迹，含事后回看验证
2026-10-12 | 3_behavior/decision_cases/README_怎么写.md | add | 新增。降低填表成本
2026-10-12 | 7_ai_training/corrected_outputs/2026-10-12_系统审计暴露的四个结构缺陷.md | add | 新增。首条修正记录
2026-10-12 | 7_ai_training/corrected_outputs/README_怎么写.md | add | 新增。格式与门槛说明
2026-10-12 | 0_system/evolution_protocol.md | rewrite | "AI 应当自动完成" → 明确的四步执行命令。新增长期进化判定标准
2026-10-12 | AGENTS.md | edit | 新增"会话结束前必须执行"章节
2026-10-12 | AI_START.md | edit | 长期记忆规则改为可执行命令
2026-10-12 | .workbuddy/rules.md | edit | 新增会话结束执行清单 + 健康指标
2026-10-12 | README.md | edit | 目录树更新（旧名 my-ai-os → ZZ-Second-Brain），新增"这个系统在进化吗"章节
2026-10-12 | zzskill/README.md | fix | 3 处安装命令仓库名 my-ai-os → ZZ-Second-Brain
2026-10-12 | .claude-plugin/marketplace.json | fix | 描述里的旧仓库名

2026-10-12 | tools/capture.py | add | 新增。会话采集器，读 AI 客户端本地日志生成待审草稿
2026-10-12 | tools/launcher.py | add | 新增。一键装 hook + 定时采集，含 status/uninstall
2026-10-12 | tools/install_hooks.py | add | 新增。沉淀守卫：改了核心规则不记日志就拦 commit
2026-10-12 | tools/LAUNCHER_启动器说明.md | add | 新增。启动器说明，含各客户端可采集性实测结论
2026-10-12 | 8_contexts/README_inbox.md | add | 新增。待审草稿区说明与处理三问
2026-10-12 | 0_system/evolution_protocol.md | edit | 新增启动器章节、自动化边界表、inbox 清理步骤
2026-10-12 | tools/README.md | rewrite | 补齐五个脚本说明与已知限制

## 这份日志本身曾经是空的

2026-05-10 到 2026-10-12，中间五次提交没有留下任何变更记录。
这不只是记录缺失——**它说明"改了要记"这条规则从未被执行过。**

一条不会被执行的规则，写下来只是安慰自己。
所以从 2026-10-12 起，它被执行流程的第一步绑定为强制步骤，
见 `0_system/evolution_protocol.md` 第 4 步。
