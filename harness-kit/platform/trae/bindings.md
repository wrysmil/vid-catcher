# Trae 平台绑定

逻辑原语 → Trae API。语义以 `core/capabilities/` 与 `core/orchestration/` 为准。

| 原语 | Trae 绑定 |
| --- | --- |
| `DetectPlatform()` | Trae 工作区 → `trae` |
| `SpawnWorker(role)` | Trae Agent 模式（`.trae/agents/<role>.md` 由平台自动加载）。只读角色靠 prompt 纪律 |
| `ParallelBatch` | Trae Agent 并行任务; max 3 |
| `WorktreeInit` | 同 `scripts/harness-worktree.sh` / git worktree |
| `StructuredAsk` | Trae structured Ask（通过 Task 工具） |
| `EmitHook` | Trae hooks 机制（可选，用户自行配置） |
| `LoadSkill(slug)` | Read `.agents/skills/<slug>/SKILL.md`（共享层）或 `.trae/skills/<slug>/SKILL.md`（平台层覆盖） |
| `LoadAgent(role)` | Read `.agents/agents/<role>.md`（共享层） |
| `LoadCapability(orchestration.dispatch)` | `orchestration` skill → core dispatcher |

**SpawnWorker 委派 prompt 必含：** WU id、wu_type、agent_role、允许文件、禁止项、done criteria、worktree_path（若启用）、本 WU Skills、返回格式。

**降级记录：** matrix 为 `degraded` 时，DISPATCH-TRACK 写 `Detail: capability <id> degraded`。

**Skill 路径：** 共享 `.agents/skills/`（含 `git-xywh`、`orchestration` 等通用 skill）；平台特有 `.trae/skills/`。
