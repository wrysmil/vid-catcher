# Harness 抽象运行时原语

平台适配器将下列原语映射到本地 API；**禁止**在适配器内重定义语义。契约详情见 `registry.md`。

| 原语 | 契约摘要 | 典型产物/副作用 |
| --- | --- | --- |
| `DetectPlatform()` | 返回 `cursor \| claude \| trae \| generic` | execution-log FM `platform` |
| `LoadCapability(id)` | 按 routing 加载 core 文档 / stage skill | 回复次行 `Skills:` |
| `StageGate(phase)` | 写入 specs/plans/decisions 后暂停 | 模板 `## Next` |
| `SpawnWorker(role, wu, context)` | 隔离上下文；不得继承 Leader 全历史 | WU 返回 `wu_status` + `### Skills 使用` |
| `ParallelBatch(workers[])` | 仅当 WU 文件集不相交；上限可配置 | DISPATCH-TRACK `Sub-agents: N` |
| `WorktreeInit(batch)` | 委派写代码类 WU 前执行 | tracking `WORKTREE-INIT` |
| `Integrate(results[])` | Leader 合并；禁止子 Agent 自声称批次完成 | plan 勾选、execution-log |
| `CollectiveTest()` | 按 `project.verification.md` | `*-collective-test.md` |
| `CollectiveReview()` | 审查实例 ≠ 任一实现实例 | `*-code-review.md` |
| `StructuredAsk(question)` | 一次一问；优先选择题 | 无文件 |
| `EmitHook(event)` | 可选；失败不阻断主路径 | 本地 hook 日志 |

## 禁止项（全局）

- Core 文档引用具体平台路径（除「见适配器 bindings」指针）
- 适配器重定义 GROUP/WU/尾盘语义
- 并行 WU 修改同一文件
- 实现与审查同一 worker 实例
- 未 Write collective-test / code-review 即声称批次完成
- 静默省略 matrix 标为 `degraded` 的能力（须在 DISPATCH-TRACK 记 `Detail: capability <id> degraded`）

## 降级协议

1. matrix `degraded` → 派发前 track 记 degraded 明细
2. matrix `manual` → 文档说明人工步骤；routing 默认路径仍可用
3. matrix `unsupported` → 不得出现在该平台 routing 默认路径
4. 绑定失败 → `platform: generic`，顺序执行，execution-log 记 `Error: spawn unavailable`
