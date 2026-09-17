# Dispatcher 工作流（平台无关）

将已批准 plan 转为并行 worker 执行。物理绑定见 `platform/<platform>/bindings.md`。

**触发：** `core/routing.md` 判定「多 task 编码 / 并行实现」。

---

## 输入

- `.ai-runtime-artifacts/plans/` 已批准 plan，或
- spec `skip:plan(reason)` 且仍属多 task

## 输出

- 代码变更
- `.ai-runtime-artifacts/execution-logs/YYYY-MM-DD-<topic>-execution-log.md`
- 可选：`tracking/DISPATCH-TRACK-<date>.md`

---

## 步骤 0：`WorktreeInit`

**做：** 将委派写代码类 worker（有 `*-dispatch.md` / DISPATCH-TRACK）时，GROUP-1 派发前。

**跳过：** routing 小改动；Leader 主线程直接实现；只读探查不改代码。

权威：`docs/superpowers/specs/2026-05-29-git-worktree-isolation-design.md` §5.4。

1. `worktree_id` = `wt-{dispatch_stem}` → `worktree_path` = `<repo-parent>/.harness-worktrees/<repo-basename>/{worktree_id}/`
2. `git worktree add -b harness/{worktree_id} <worktree_path> <base>`（可复用）
3. tracking 记 `WORKTREE-INIT`；更新 HANDOFF § Git 沙箱

**门禁：** 将委派写代码 WU 时，未完成步骤 0 **不得**派发。

## 步骤 0.5：`ContextPack`（上下文打包）

Leader 在派发 WU 前执行上下文打包，为每个 Worker 准备精确上下文。原理见 `context-engineering` skill。

**前置步骤（必执行）：** 在开始打包前，Leader 必须先执行 `source-driven-development` Step 0 — 扫描 `.ai-runtime-artifacts/` 中与当前 GROUP/任务相关的 specs、plans、decisions、contracts、research。找到的产物将成为后续打包的 L2 输入。

### 打包流程

对每个 WU，Leader 按以下顺序准备 WU Context Block：

```
Step 1: 确定相关 Rules + Spec 章节（不是全文，是节选）
Step 2: 确定相关源文件（≤5 个）+ 测试文件
Step 3: 找到参考范例（codebase 中已有相似实现）
Step 4: 明确约束（"不要碰 X/Y/Z"）
Step 5: 附加接口契约（如有跨 WU 依赖，从 `.ai-runtime-artifacts/contracts/` 读取）
Step 6: 附加切片建议（incremental-implementation 三策略之一）
Step 7: 打包为 WU Context Block → 随 WU 派发 prompt 传递
```

### 强制检查打包

Leader 在派发前须确保 WU Context Block 包含各 Agent 内嵌检查表的适用条目。子 Agent 返回时须对照检查表给出执行结果。

### 五级上下文层级

```
L1: Rules Files (project.profile.md, CLAUDE.md)  ← 始终加载
L2: Spec / Architecture Docs (相关章节)           ← 按 Feature 加载
L3: Relevant Source Files (≤5 个)                ← 按 Task 加载
L4: Contract / Interface Definitions             ← 跨 WU 时加载
L5: Error Output / Test Results                  ← 按 Iteration 加载
```

### 目标：每个 WU ≤2000 行聚焦信息

### Tier 1 自打包

Tier 1 Leader 直做时，Leader 在开始写代码前对自己执行上述打包流程（Self-Context Pack），确保同样有精确上下文。跳过 L5（无历史错误输出）。

**跳过：** Tier 0 单文件机械修改不触发上下文打包。

## 步骤 1：执行图

从 plan 提取 WU（有界 / 可验证 / 文件不相交）。写入 `*-dispatch.md`（模板 `dispatch.harness-overlay.md`）：

```markdown
## 执行图

GROUP-1（并行）:
  WU-01: <描述> | 文件: a.ts | 依赖: 无 | wu_type: feature | agent_role: coder | wu_skills: auto
```

`wu_skills: auto` → `core/orchestration/skill-preferences.md` § 默认路由表。

## 步骤 2：`ParallelBatch` / `SpawnWorker`

对 GROUP 内无未完成依赖的 WU，**并行** `SpawnWorker(agent_role, wu)`（文件不相交；≤ `max_parallel`，硬顶 5）。实现 = `Agent(subagent_type=<agent_role>)`，**必须显式传 subagent_type 映射到 `<role>`**——漏传会回退到通用子代理，`.claude/agents/<role>.md` 的检查表/完成定义/返回格式不加载。

| agent_role | 说明 |
| --- | --- |
| coder | 实现+单测+轻量审查+自检 |
| implementer | docs/chore/config |
| test-engineer | 测试/E2e 资产 |
| smoke-tester | 提测前冒烟场景跑（agent-browser / chrome-devtools-mcp） |
| web-investigator | 调研取证 |
| explorer | 只读探查 |
| debugger | 缺陷调查+根因修复 |
| reviewer | 代码审查（只读） |
| security-auditor | 安全审查（只读，OWASP + LLM 安全） |
| perf-auditor | 性能审查（只读，CWV + N+1 + Bundle） |
| code-simplifier | 代码简化（Chesterton's Fence → 逐个变更） |

**禁止** Leader 主线程改业务代码（小改动除外）。

**委派 prompt（中文、简练）：**

| 项 | 内容 |
| --- | --- |
| WU 身份 | `WU-<id>` + `wu_type` + `agent_role`；派发时在 prompt 首句写明。点明的是 **WU 身份**，不是**角色人格** —— 禁止写「你是 Harness Coder」这类角色样板，角色文件由平台子代理机制自动加载 |
| 目标/Done | 各 1–3 句 |
| 范围 | 允许文件；禁止项一句 |
| Skills | slug → 路径（禁只写 `auto`） |
| 验证 | 命令 |
| cwd | 沙箱批次：`worktree_path: <abs>` |
| 返回 | `wu_status`、`### Skills 使用`（coder 含 `code_review`/`self_check`） |

Leader 解析 `auto` → 抄 slug+路径入 prompt；无 `### Skills 使用` **不整合**。

**派发调用示例（平台适配原则）——核心是「传 role 名 + 让平台子代理机制自动加载」：**

```
❌ 错误（手写角色样板，等于把平台自动加载重复实现了一遍）：
  Agent({ description: "WU-01", prompt: "你是 coder 子代理，先读 coder.md，按 coder.md 的返回格式输出..." })

✅ 正确（传 role 名，让平台子代理机制自己加载）：
  Agent({ subagent_type: "coder",    description: "WU-01", prompt: "实现 X，只改 a.ts/b.ts，验收：..." })
  Agent({ subagent_type: "reviewer", description: "WU-02", prompt: "审查 WU-01 变更，只读，输出见 spec..." })
  // Cursor 用 "Use coder subagent"，Trae 用 "Agent 模式 + coder role"，语义等价

✅ 正确（prompt 首句点明 **WU 身份**）：
  prompt: "你是 WU-01，wu_type=feature，agent_role=coder。任务：实现 X...
```

**禁传 worker：** `brainstorming`、`writing-plans`、`orchestration`、`git-xywh`。

## 步骤 3：整合与尾盘

单 WU 返回：验证字段 → Leader 更新 plan/tracking。**不写批次完成态。**

GROUP 收尾（`docs/superpowers/specs/2026-05-28-batch-closeout-review-and-collective-test.md` §4）：

1. **A 集体测试** — Load `verification-before-completion`；cwd=`worktree_path`；Write `.ai-runtime-artifacts/verifications/*-collective-test.md`（含检查表执行结果）；FAIL → STOP

2. **B 多层并行审查** — 并行扇出 3 个审查 Agent：

   ```
   Leader 并行 SpawnWorker:

   ┌────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │ Reviewer (增强) │  │ Security-Auditor  │  │ Perf-Auditor      │
   │ agent_role:     │  │ agent_role:       │  │ agent_role:       │
   │ reviewer        │  │ security-auditor  │  │ perf-auditor      │
   │ wu_type: review │  │ wu_type: review   │  │ wu_type: review   │
   │ 只读            │  │ 只读               │  │ 只读(按需)        │
   └───────┬────────┘  └────────┬─────────┘  └────────┬─────────┘
           │                    │                       │
           └────────────────────┼───────────────────────┘
                                ▼
                     Leader 合并审查报告
   ```

   - **Reviewer**: Load `code-review-and-quality` + `requesting-code-review`。五轴审查（正确性/可读性/架构/安全概览/性能概览）+ 8 种重构建议。Leader Write `.ai-runtime-artifacts/reviews/*-code-review.md`
   - **Security-Auditor**: Load `security-and-hardening`。OWASP Top 10 + LLM 安全检查 + npm audit。Leader Write `.ai-runtime-artifacts/reviews/*-security-review.md`
   - **Perf-Auditor**（按需，UI/API/DB WU 时启用）: Load `performance-optimization`。CWV + N+1 + Bundle + INP。Leader Write `.ai-runtime-artifacts/reviews/*-perf-review.md`

   **门禁**: 任一审查 BLOCK → 对应 WU 需修复后重新审查。

3. **C [可选] Simplify Pass** — Reviewer 标记"过于复杂"时，Leader 启动 `code-simplifier`（`agent_role: code-simplifier, wu_type: simplify`）。Load `code-simplification`。在 worktree 内执行简化，保持测试不变。与功能变更分离 commit。

4. **D 关闭** — execution-log 链接审查产物；Leader 汇总所有子 Agent 返回的检查结果 → 补充自检 → 写入 collective-test.md；APPROVE/SKIPPED + 测试 PASS 方可声称完成

## 步骤 4：追踪

1. 创建 `DISPATCH-TRACK-<date>-<topic>.md`
2. 每 WU append（`tracking/schema.md`）
3. 可选 CHECKLIST；上下文重置写 HANDOFF

## 步骤 5：WORKTREE-CLOSE

曾 INIT 且批次完成、用户确认 Git 后：`git worktree remove`；tracking 记 `WORKTREE-CLOSE`。

---

## 角色索引

`agent_role` 与 `.claude/agents/<role>.md` 同名映射。派发走各平台原生 role 子代理（`platform/<platform>/bindings.md`），角色文件由平台自动加载。

## Superpowers 衔接

| 阶段 | Skill |
| --- | --- |
| 需求澄清（按需） | `interview-me` |
| 设计 | `brainstorming` + `source-driven-development`（STACK DETECTION） |
| 接口契约 | `api-and-interface-design` |
| 计划 | `writing-plans` |
| 上下文打包 | `context-engineering` |
| 实现 | `orchestration`（统一编排，平台无关）|
| 尾盘测试 | `verification-before-completion` |
| 尾盘审查 | `requesting-code-review` + `code-review-and-quality` + `security-and-hardening` |
| 尾盘简化（按需） | `code-simplification` |
| 发布（按需） | `shipping-and-launch` + `observability-and-instrumentation` |

## 反模式

- 未读 plan 派发；单 worker 包整个 epic
- 实现与审查同实例；跳过 execution-log / 尾盘产物
- 有委派无 WORKTREE-INIT；无委派仍 INIT
- Leader 自动 push
- 跳过上下文打包直接派发（Worker 信息不足→幻觉或过载→失焦）
- **派发退通用子代理 / 手写角色样板进 prompt** → 角色 checklists/完成定义/返回格式未加载，违反平台子代理机制
- 尾盘审查只跑一个 reviewer，缺少安全审查维度
- Leader 直做（Tier 1）不执行自上下文打包
