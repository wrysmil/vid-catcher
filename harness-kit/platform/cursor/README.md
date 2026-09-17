# Cursor Adapter

Cursor 适配分两层：

1. **投影层**（bootstrap 复制到项目根）：`.cursor/rules/`、`.agents/agents/`（共享子 Agent）、`.agents/skills/`（共享能力副本）
2. **绑定层**（留在 `harness-kit/platform/cursor/`）：`bindings.md`、`capability-matrix.yaml`；编排 stub 重定向至 `core/orchestration/`

## 投影后应具备

- `.cursor/rules/ai-entry.mdc`、`cursor-subagent-routing.mdc`
- `.agents/agents/<role>.md`（共享层 agent manifest，Worker 角色 + 内嵌检查表）
- `.agents/skills/` 能力副本；WU skill 偏好 → `core/orchestration/skill-preferences.md`
- `.agents/skills/orchestration/SKILL.md`

## 关键文档

| 文档 | 用途 |
| --- | --- |
| `../../core/orchestration/dispatcher-workflow.md` | 编排唯一步骤源 |
| `bindings.md` | Cursor 原语映射 |
| `capability-matrix.yaml` | parity 审计 |
| `../../core/orchestration/platform-adapters.zh.md` | 平台检测与角色映射 |
| `../../core/routing.md` | 路由权威 |

上游改编来源见 `VENDOR.md`。

## 接入

先 `init/onboarding-handoff.txt`，再 `bash harness-kit/scripts/harness-project.sh project`（一次性投影 `.cursor/`、`.agents/`）。

## Hooks

Hooks 扩展已移除；如需 session 提示注入，请在 `.cursor/hooks.json` 中手动配置。
