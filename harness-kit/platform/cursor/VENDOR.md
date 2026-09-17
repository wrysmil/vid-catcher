# 上游来源

| 字段 | 值 |
| --- | --- |
| 上游 skill | harness-engineer |
| 版本 | 5.3.1 |
| 源路径 | `~/.cursor/skills/harness-engineer-5.3.0/` |
| 改编日期 | 2026-05-24 |
| Phase 3 完成 | 2026-05-24 |
| harness-kit 方案 | 方案 B（见 `platform/cursor/README.md`） |

## 版本钉扎策略

1. **不**整包 vendoring harness-engineer；仅 fork 列于下表的文件。
2. 上游升级时：对比 `~/.cursor/skills/harness-engineer-5.3.0/`，更新本目录对应文件，并递增本表「改编日期」。
3. 重大差异写入 `platform/cursor/README.md` 或本文件「未引入模块」。
4. `_meta.json` 上游版本：**5.3.1**（slug: harness-engineer）。

## 本目录改编来源

| harness-kit 文件 | 上游文件 |
| --- | --- |
| `platform-adapters.zh.md` | `references/platform-adapters.md` |
| `dispatcher-workflow.md` | `agents/dispatcher.md` |
| `agents/leader.md` | Leader 行为规范（投影至 `.cursor/rules/leader.mdc`） |
| `agents/implementer.md` | `.agents/agents/implementer.md` |
| `agents/reviewer.md` | `.agents/agents/reviewer.md` |
| `agents/debugger.md` | `.agents/agents/debugger.md` |
| `tracking/schema.md` | `runtime/status-management.md` |
| `context-budget.md` | `runtime/context-engineering.md` |
| `model-routing.yaml` | `platform-adapters` + 模型路由表（手写） |
| `artifact-templates/dispatch-track.md` 等 | 新建（harness-kit 产物契约） |
| `continuous-loop.md` | `runtime/loop.md`（摘要 + harness-kit 映射） |
| `orchestration/hooks/README.md` | `runtime/hook-system.md` |
| `.cursor/hooks.json.example` | 新建（Cursor 原生 hooks） |
| `config.defaults.yaml` | `CONFIG.yaml`（简化） |
| `.cursor/rules/cursor-subagent-routing.mdc` | Rule 1–15 + platform-adapters + 阶段门禁 |
| `.agents/agents/*.md` | 共享层 agent manifest（Worker + 内嵌检查表） |
| `.cursor/skills/*/` 能力副本 | 自全局 superpowers 等复制，见 `_vendor-sources.yaml` |
| `orchestration/skill-preferences.zh.md` | 任务 ↔ skill 偏好（文档维护，`auto` 查表） |
| `.agents/skills/orchestration/SKILL.md` | dispatcher 摘要（指向完整 workflow） |

## 未引入的上游模块

- `PLATFORM_REQUIREMENTS.md`（HALT 语义）→ 降级为 `CURSOR-PRECHECK.md`
- `runtime/loop.md` 全文 → 摘要见 `continuous-loop.md`
- `tools/tool-router.md`
- `docs/status/` 目录约定 → 合并至 `.ai-runtime-artifacts/execution-logs/`
