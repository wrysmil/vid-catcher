# .agents — 共享层

本目录是 harness-kit 的**平台无关共享层**，Cursor / Claude Code / Trae 均引用。

## 目录结构

```
.agents/
├── skills/         ← 共享 skills（13 个，含 git-xywh + trae-orchestration）
├── agents/         ← 共享 agent manifests（7 个）
└── README.md
```

## 共享 Skills（`.agents/skills/`）

| slug | 用途 | 来源 |
| --- | --- | --- |
| test-driven-development | 先测后实现 | superpowers（副本） |
| verification-before-completion | 完成前须有命令证据 | superpowers（副本） |
| systematic-debugging | 根因调查 | superpowers（副本） |
| requesting-code-review | 独立审查 | superpowers（副本） |
| receiving-code-review | 按审查意见改代码 | superpowers（副本） |
| ui-ux-pro-max | UI/UX 设计系统与可检索设计库 | Trae skills（整目录副本） |
| frontend-design | UI 实现审美 | 全局复制 |
| agent-browser | 浏览器自动化（需 `infsh`） | 全局复制 |
| document-review | 文档审查 | 内置 |
| git-xywh | 组织 Git 工作流规范 | 从 cursor 迁移 |
| cursor-orchestration | Cursor 编排调度 | 内置（→ core dispatcher） |
| claude-orchestration | Claude 编排调度 | 内置（→ core dispatcher） |
| trae-orchestration | Trae 编排调度 | 新增（→ core dispatcher） |

来源登记：`_vendor-sources.yaml`

## 共享 Agent Manifests（`.agents/agents/`）

由 Claude Code / Cursor / Trae 直接加载。Worker 角色 + 内嵌检查表的完整定义。Leader 行为规范见 `platform/<platform>/<rules>/leader.md`。

| 文件 | 角色 |
| --- | --- |
| coder.md | 资深开发者 |
| implementer.md | 轻量执行 Worker |
| reviewer.md | 独立审查者 |
| test-engineer.md | 测试工程师 |
| debugger.md | 缺陷调查专家 |
| explorer.md | 只读探查者 |
| web-investigator.md | 网探 |

## 平台特有扩展

| 平台 | 目录 | 内容 |
| --- | --- | --- |
| Cursor | `platform/cursor/.cursor/` | rules、hooks |
| Claude Code | `platform/claude/` | bindings、capability-matrix |
| Trae | `platform/trae/` | bindings、capability-matrix |

## 优先级

平台层可覆盖共享层（如同名 skill，平台层优先）。项目级 skill 只放真正属于本项目的能力。

若 `.agents/` 中的规则与平台层规则冲突，以项目级规则和 `AGENTS.md` 为准。
