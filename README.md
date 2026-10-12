# 周正 AI 人格操作系统 (AI Personality OS)

> 版本：2.0 | 格式：纯 Markdown | 兼容：所有主流 LLM
> 原则：可移植 · 可进化 · 人格核心 · 可商业化

## 这是什么

这不是普通的知识库。这是**周正的个人 AI 操作系统**。

目标：构建一个第二大脑，能够——
- 像周正一样思考
- 像周正一样决策
- 像周正一样表达
- 持续学习与进化
- 长期保存认知
- 具备商业复用价值

## 系统结构

```
ZZ-Second-Brain/
├── 0_system/          # 系统规则与协议
├── 1_identity/        # 人格与身份
├── 2_cognition/       # 思维与认知
├── 3_behavior/        # 行为与执行
│   └── decision_cases/# 真实决策轨迹 ← 不可替代的资产
├── 4_expression/      # 表达与创作
├── 5_business/        # 商业与变现
├── 6_memory/          # 记忆与经验
├── 7_ai_training/     # AI 训练数据
│   └── benchmark_outputs/ # 人格一致性基准测试
├── 8_contexts/        # 上下文管理
├── 9_meta/            # 元数据与进化
├── tools/             # 可执行装置（机检 + 闭环扫描）
└── AGENTS.md          # AI 读取入口
```

## 这个系统在进化吗

`tools/evolve.py` 会扫描六个沉淀目录，报告哪些还是空模板：

```bash
python tools/evolve.py
```

输出的"总计：N 份实际内容"是**唯一客观指标**，不靠感觉判断。
如果长期不变，说明系统已停转——此时继续往 `0_system/` 加规则
只会让规则更厚、判断不会更准。

## 一次性装上启动器

```bash
python tools/launcher.py install
```

装完之后自动发生三件事：

| 机制 | 效果 |
|------|------|
| pre-commit hook | 改了 `0_system/` 或 `1_identity/` 却没记变更日志 → **拦住 commit** |
| pre-push hook | 每次 push 前自动打印闭环体检 |
| 定时采集（每 2 小时） | 从 AI 客户端本地日志捞新会话，生成待审草稿到 `8_contexts/inbox/` |

**但有一件事必须说清楚：**

AI 客户端不会把对话推送给这个仓库。"连上就自动收录"做不到全自动。
`capture.py` 的办法是**读客户端写在本地硬盘上的会话日志**——
客户端不写本地日志的，就采不到。

2026-10-12 实测：

| 客户端 | 能否采到正文 |
|--------|------------|
| Claude Code | ✅ `~/.claude/projects/**/*.jsonl` 完整对话 |
| Codex | ⚠️ 结构相近，本机暂无日志可验证 |
| WorkBuddy | ❌ `workbuddy.db` 只有元数据，正文不在本地 |

自动化到哪一步为止：

| 环节 | 能不能自动 |
|------|-----------|
| 捞对话、生成草稿 | ✅ |
| 拦没记日志的提交 | ✅ |
| push 前体检 | ✅ |
| **判断哪条值得沉淀** | ❌ 故意不做——自动判断会把垃圾和金子一起捡 |
| **提供真实客户决策** | ❌ AI 代替不了，编的会污染系统 |

详见 `tools/LAUNCHER_启动器说明.md`。

## 核心原则

- **记录推理，而非结果** — AI 从推理中学习认知
- **存储决策逻辑** — 每个决策包含情境、假设、选择原因
- **存储负面偏好** — 讨厌什么比喜欢什么更重要
- **模型无关** — 纯 Markdown，兼容所有 AI 模型
- **高信号密度** — 不说废话，不堆概念
- **永远在进化** — 系统永不完成

## 使用方法

1. 所有 AI 进入本仓库，**必须先读取 AI_START.md**
2. 按需读取对应模块文件
3. 持续通过 6_memory/ 和 7_ai_training/ 迭代进化

## 作者

**周正** — 一个见过社会另一面的创业人

## 多平台兼容

本仓库已适配以下 AI 平台，进入即自动识别：

| 平台 | 入口文件 | 状态 |
|------|----------|------|
| **Codex** (OpenAI) | `AGENTS.md` + skills/ | ✅ 原生支持 |
| **Claude Code** (Anthropic) | `CLAUDE.md` | ✅ 自动加载 |
| **WorkBuddy** | `.workbuddy/config.json` + `.workbuddy/rules.md` | ✅ 自动加载 |
### 如何使用

#### 对于 AI Agent 平台
直接 clone 本仓库，AI 会自动识别入口文件。

#### 对于通用 LLM（ChatGPT Web、Gemini 等）
1. 复制 `AGENTS.md` 的内容作为系统提示词
2. 或把整个仓库作为知识库上传

#### Skill 触发
无论哪个平台，以下触发词都有效：
- `/商业诊断` — 商业模式诊断
- `/对标` — 对标分析
- `/内容诊断` — 内容创作诊断
- `/hook` — 开头优化
- `/小红书标题` — 标题公式
- `/AI检测` — AI 特征识别
- `/目标` — 目标清晰化
- `/决策` — 决策系统
- `/action` — 执行力诊断
- `/好问题` — 问题改写

详见 `skills/` 目录。

### 迁移到新平台

如果你用的 AI 不在以上列表中，用本仓库的 Agent 迁移工具：
1. 输入 `/agent迁移` 触发
2. 指定目标平台
3. 自动生成对应格式的入口文件
## zzskill 商业工具箱（完整集成）

本仓库集成了完整的商业诊断工具箱，用于「周正商业IP」的诊断与内容服务。
### 包含内容

- **33 个 Agent Skill**（`zzskill/skills/`）——32 个业务 Skill + 1 个系统更新入口
- **17 个深度知识包**（`zzskill/知识库/Skill知识包/`）
- **原子化知识库**（`zzskill/知识库/原子库/`）— 4,176 个知识原子，从 16,152 条公开推文提炼
- **公开推文集**（`zzskill/books/`）
- **路由系统**：`/zz` 按任务复杂度判断单 Skill 或主辅组合，并生成可直接发送的提示词
- **多语言文档**：简体中文 / English / 日本語 / 한국어 / 繁體中文
- **多平台支持**：豆包、WorkBuddy、Claude Code、Codex

### Skill 完整列表

| 分类 | Skill |
|------|-------|
| 商业诊断 | `zz` · `zz-diagnosis` · `zz-benchmark` · `zz-action` · `zz-goal` |
| 思考工具 | `zz-theory-grounding` · `zz-standard-answer` · `zz-deconstruct` · `zz-good-question` · `zz-jtbd` · `zz-chatroom` · `zz-chatroom-austrian` |
| 内容创作 | `zz-content` · `zz-hook` · `zz-xhs-title` · `zz-ai-check` · `zz-wechat-html` · `zz-video-extract` · `zz-content-risk-check` · `zz-resonate` · `zz-script-flow` · `zz-spread` |
| 状态管理 | `zz-save` · `zz-restore` · `zz-report` · `zz-decision` |
| 学习 | `zz-learning` |
| 工作台基建 | `zz-update` · `zz-content-system` · `zz-knowledge` · `zz-agent-migration` · `zz-install-skill` · `zz-skill-maker` |

每个 Skill 的适用时机、输入示例与产出，见 [`zzskill/docs/新手入门.md`](zzskill/docs/新手入门.md)。
