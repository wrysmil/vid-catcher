---
name: orchestration
description: 多任务并行编排调度。已批准 plan +「开始实现」后并行派发 WU。平台无关；物理绑定见 platform/<platform>/bindings.md。触发：并行实现、多 task、开始实现、编排。
---

# Orchestration（统一编排）

**前置：** 已批准 plan；用户说「开始实现」。未批准不得激活。

**平台：** 本 skill 平台无关。SpawnWorker 具体机制见 `platform/<platform>/bindings.md`。禁用平台原生 plan 工具（见 `routing.md` § 平台原生 plan 工具）。

## 激活后

1. 声明 `「Harness：orchestration:dispatcher-workflow」`
2. Read **`harness-kit/core/orchestration/dispatcher-workflow.md`**
3. Read `tracking/schema.md`、已批准 plan、`project.verification.md`
4. 委派写代码 WU：**WORKTREE-INIT** → 并行派发

## SpawnWorker

各平台子 Agent 委派机制见对应适配器：

| 平台 | 绑定文件 | 机制摘要 |
| --- | --- | --- |
| Claude Code | `platform/claude/bindings.md` | `Task(subagent_type=generalPurpose)` + core agent 文件为 prompt |
| Cursor | `platform/cursor/bindings.md` | `.agents/agents/<role>.md` subagent |
| Trae | `platform/trae/bindings.md` | Trae Agent 模式 + core agent 文件 |

通用 agent_role 映射见 `core/orchestration/dispatcher-workflow.md` § 步骤 2。`wu_skills: auto` → `core/orchestration/skill-preferences.md`。

**尾盘：** collective-test → 并行扇出 reviewer + security-auditor（+ perf-auditor 按需）→ Leader 落盘产物。

## 禁止

- 未过 plan 门禁
- Leader 写业务代码（小改动除外）
- 实现与审查同实例
- 跳过 DISPATCH-TRACK / 尾盘产物
- 末 WU 返回即声称完成
- 使用平台原生 plan 工具（EnterPlanMode / Cursor Plan 模式等）
