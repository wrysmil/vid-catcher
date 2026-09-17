# Cursor 平台绑定

逻辑原语 → Cursor API。语义以 `core/capabilities/` 与 `core/orchestration/` 为准。

| 原语 | Cursor 绑定 |
| --- | --- |
| `DetectPlatform()` | `.cursor/` + subagent 可委派 → `cursor` |
| `SpawnWorker(role)` | `Use <role> subagent`（`.cursor/agents/<role>.md` 由平台自动加载）。只读角色靠 prompt 纪律 |
| `ParallelBatch` | 并行 Task/subagent，≤5 |
| `WorktreeInit` | `scripts/harness-worktree.sh` 或 git worktree 步骤 |
| `StructuredAsk` | `AskQuestion` |
| `EmitHook` | Cursor hooks 机制（可选，用户自行配置） |
| `LoadSkill(slug)` | Read `.agents/skills/<slug>/SKILL.md`（共享层）或 `.cursor/skills/<slug>/SKILL.md`（平台层覆盖） |
| `LoadAgent(role)` | Read `.agents/agents/<role>.md`（共享层） |
| `LoadCapability(orchestration.dispatch)` | `orchestration` skill → core dispatcher |

**Skill 路径：** 共享 `.agents/skills/`（含 `git-xywh` 等通用 skill）；平台特有 `.cursor/skills/`。

**降级：** 见 `capability-matrix.yaml`。
