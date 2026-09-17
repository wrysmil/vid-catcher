# 编排追踪日志 Schema

状态保存在仓库文件中，**不**依赖上下文窗口。改编自 harness-engineer `runtime/status-management.md`。

**根目录：** `.ai-runtime-artifacts/execution-logs/tracking/`

---

## 文件层级

| 文件 | 用途 | 写入者 |
| --- | --- | --- |
| `DISPATCH-TRACK-<YYYY-MM-DD>-<topic>.md` | 并行 WU / ITR 逐步追踪 | Leader |
| `CHECKLIST-<topic>-WU-<id>.md` | 单 WU done criteria | Leader 创建；勾选由 **Leader** 更新（见 `runtime/plan-progress-sync.md`） |
| `../HANDOFF.md` | 上下文重置检查点（覆盖写） | Leader |
| `../PROGRESS.md` | 周期级紧凑摘要（可选） | Leader |

模板见 `dispatch-track.md`、`handoff.md`、`progress.md`、`wu-checklist.md`；plan 配对执行图见 `dispatch.harness-overlay.md`（`.ai-runtime-artifacts/plans/*-dispatch.md`）。

---

## 通用条目格式（append-only）

每条追踪**追加**到文件末尾，**禁止**改删历史行：

```text
[YYYY-MM-DD HH:MM] <PHASE>-<STEP> | <AGENT> | Status: <started|completed|blocked|recovering>
Detail: <事实一句>
Sub-agents: <活跃 Task 数>
Context: ~<XX>%
Output: <产物路径或 none>
Error: <错误或 none>
Next: <下一步>
```

| 字段 | 说明 |
| --- | --- |
| PHASE-STEP | 如 `DISPATCH-GROUP-1`、`WU-02-implement` |
| AGENT | `Leader` / `Implementer` / `Reviewer` / `Debugger` |
| Status | started → completed；blocked 需人工或 Leader 决策 |

---

## DISPATCH 专用字段

并行编排时在 Detail 后可选追加：

```text
GROUP: <N> | WU: <id> | ITER: <n> | STEP: implement|test|review|done
WorktreeId: wt-<stem> | WorktreePath: <abs-path> | Branch: harness/wt-<stem> | Base: <sha>
Tests: <pass/fail 摘要>
Queue-remaining: WU-03, WU-04
Reviewer: separate-task | pending
Worktree: <path or n/a> | Branch: <name or n/a> | Title(zh): <wu_title_zh>
Closeout: collective-test=<path|pending> verdict=PASS|FAIL|n/a | code-review=<path|pending> verdict=APPROVE|BLOCK|SKIPPED|n/a | status=pending|in-progress|done
```

**Closeout 行**（gap #10）：GROUP 收尾时由 Leader 追加，引用 `verifications/*-collective-test.md` 与 `reviews/*-code-review.md` 路径及 verdict。`status=pending` 表示本 GROUP 尚有 WU 未完成；`in-progress` 表示 WU 全部完成、closeout 流程进行中；`done` 表示 A 集体测试 + B 集体审查均通过（或合法 SKIPPED）可声称本 GROUP 交付完成。细则见 `docs/superpowers/specs/2026-05-28-batch-closeout-review-and-collective-test.md`。

### 路径位置（consumer 侧 vs harness-kit 仓库）

Closeout 引用的**路径**与仓库的**位置**有关，harness-kit 自身**不**消费此流程：

- **消费者项目**（`harness-init` 出来的项目）：closeout 产物落在 `.ai-runtime-artifacts/verifications/`、`.ai-runtime-artifacts/reviews/`、`.ai-runtime-artifacts/execution-logs/`（**不**入 .gitignore）。`scripts/harness-check.sh` 的 closeout ERROR 门禁段在消费者仓库**会**触发。
- **harness-kit 仓库自身**：`.ai-runtime-artifacts/` 被 `.gitignore` 排除（设计：harness-kit 是工具/规则，不消费自家 closeout 流程），所以 harness-kit 仓库内 closeout 产物**示例**放 `docs/runtime/closeouts/`（可入库），仅作为 consumer-side 模板参考。harness-check 在 harness-kit 仓库内**不**触发 closeout 段——这是**符合设计**的行为。

> 来源：`docs/runtime/closeouts/2026-06-12-tracking-schema-closeout-collective-test.md` § 路径位置说明。

---

## 中断恢复协议

1. 打开当前 `DISPATCH-TRACK-*.md`
2. 找最后一条 `Status: completed` 的 WU/步骤
3. 对无 `completed` 的 WU，从其最后 `started` 步骤继续
4. 若存在 `HANDOFF.md` 且比 track 新 → 先读 HANDOFF 再恢复（含 § Git 沙箱 `worktree_path`）
5. **不要**重跑已有 `APPROVE` 审查的 WU
6. 曾 WORKTREE-INIT 的批次：写代码类 WU 在 `worktree_path` 继续；未 INIT 则在主 checkout

### Leader 恢复话术

```text
从 DISPATCH-TRACK-<file> 恢复：最后完成 WU-<id>。
继续 GROUP-<n> 中 WU-<id> 的 <step>。
```

---

## 与 execution-log 关系

- **tracking/**：过程逐步日志（可很长，append-only）
- **execution-log**：任务收尾摘要（front matter + 变更列表 + 验证状态）

完成编排后，execution-log 的 `source` 应引用对应 `DISPATCH-TRACK-*.md`。
