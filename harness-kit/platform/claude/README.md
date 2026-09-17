# Claude Code 适配器

第二参考实现：Task 并行 + core 编排语义。

## 接入

1. 根目录 `CLAUDE.md` + `AGENTS.md`
2. 投影 skill：`bash harness-kit/scripts/harness-project.sh project`（含 `orchestration` skill）
3. 多 task 实现：Load **`orchestration`** → `core/orchestration/dispatcher-workflow.md`

## 平台检测

`CLAUDE.md` 会话 + Skill 工具 + 无 Cursor → `platform: claude`

## 与 Cursor 差异

| 能力 | 状态 |
| --- | --- |
| `interaction.structured-ask` | supported — AskUserQuestion 工具 |
| `orchestration.continuous-loop` | manual — 多会话 HANDOFF |
| Task `ci-investigator` | degraded — generalPurpose + 只读 |

parity 全表：`capability-matrix.yaml`。绑定：`bindings.md`。

## Hooks

仅保留 `block-native-plan-mode.sh`（PreToolUse，阻断原生 `EnterPlanMode` / `ExitPlanMode`，防止 plan 绕过 `.ai-runtime-artifacts/plans/` 落盘）。默认**不启用**，需手动 `cp .claude/settings.json.example .claude/settings.json`。

原 `harness-session-init.sh` / `harness-subagent-stop.sh` 已移除：其注入内容现由 `.claude/rules/leader.md`（会话自动注入）与 `core/routing.md`（平台无关规则）承载，无需 hook 重复注入。
