# 启动器 — 装完就不用再想了

> 一句话：**`python tools/launcher.py install`**

## 先说清楚它做不到什么

你想要的"打开任何 AI，连上就自动收录"——**"自动收录对话"这一环做不到**。

原因不在脚本，在客户端：**没有任何 AI 会把对话推送给你的 GitHub 仓库。**
Claude Code、WorkBuddy、Codex、ChatGPT Web，都是它自己的数据，不外发。

唯一的绕法：**读客户端写在你自己硬盘上的会话日志。**
`capture.py` 干的就是这件事。它只读，不写、不删、不改任何客户端数据。

## 实测各客户端可采集性（2026-10-12）

| 客户端 | 日志位置 | 能采到正文吗 |
|--------|---------|------------|
| **Claude Code** | `~/.claude/projects/**/*.jsonl` | ✅ 完整对话，含时间戳、工作目录、问答轮次 |
| **Codex** | `~/.codex/sessions/**/*.jsonl` | ⚠️ 结构相近，本机暂无日志可验证 |
| **WorkBuddy** | `~/.workbuddy/workbuddy.db` | ❌ **只有元数据，正文不在本地库** |

WorkBuddy 这条是实测结论：`workbuddy.db` 的 `sessions` 表有 101 条记录，
但字段只有 `title`/`cwd`/`model`/`timestamps` 等元信息，**没有对话正文**。
所以这个仓库的对话，你得在客户端里手动导出或复制。

**换客户端时先跑 `python tools/capture.py` 探测，不要假设能采到。**

## 三层自动化

### 第一层：自动（不需要你参与）

| 机制 | 装在哪 | 干什么 |
|------|--------|--------|
| pre-commit hook | `.git/hooks/` | 改了 `0_system/` 或 `1_identity/` 却没记变更日志 → **拦住 commit** |
| pre-push hook | `.git/hooks/` | 每次 push 前自动打印闭环体检报告 |
| 定时采集 | 系统计划任务 | 每 2 小时把新会话变成待审草稿 |

### 第二层：半自动（AI 做判断，你做确认）

草稿生成在 `8_contexts/inbox/`。每份草稿开头有同一个三问：

1. 里面有没有一个**真实的决策**（做了什么选择、被否了什么、结果如何）？
2. 有没有一条 **AI 说错了、你纠正了**的地方？
3. 有没有一个**当时以为对、后来被验证是错的**判断？

让任意 AI 读草稿、答三问、有条"是"就提炼进对应目录。**这是脚本故意不做的一步**——
自动判断价值会把垃圾和金子一起捡进去。

### 第三层：纯人工（AI 代替不了）

**真实客户决策只有你知道。** 往 `3_behavior/decision_cases/` 写 20 条以上，
这套系统才真正开始工作。AI 编的数字一旦混进去，整套系统的可信度归零。

## 常用命令

```bash
python tools/launcher.py install     # 装 hook + 定时采集
python tools/launcher.py status      # 看当前状态
python tools/launcher.py uninstall   # 全部卸掉

python tools/capture.py --days 3 --draft   # 手动采集（效果等同于定时任务）
python tools/evolve.py                     # 闭环健康扫描
python tools/lint_output.py 某文件.md      # 形式层机检
```

## 已知限制

**hook 只存在于本地 clone，不随 git 同步。**
换机器或重新 clone 后要重跑 `install`。这是 git 的机制决定的，不是遗漏。

**定时任务可能装不上。**
部分环境会拦截 `schtasks`（Windows 计划任务）。
装不上时脚本会给出替代命令，不影响 git hook。
没有定时任务只是采集变手动，沉淀质量不打折。

**确实需要跳过拦截时**：`git commit --no-verify`
