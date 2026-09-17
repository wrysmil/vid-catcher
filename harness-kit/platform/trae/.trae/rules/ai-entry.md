# Trae 统一入口

## 规范优先级

1. `harness-kit/core/routing.md` — 路由、阶段门禁、按判定加载（强制）
2. 本文件 § 文件写入与阶段门禁（强制）
3. 根目录 `AGENTS.md` — Harness 覆盖层

## 文件写入与阶段门禁

细则：`routing.md` § 阶段门禁、§ 用户话术 → Route。

**文件写入**

- 改仓库内文本（源码、配置、`.ai-runtime-artifacts/`）**只用** Write 工具；改前先 Read。
- **Shell 仅用于** 测试、lint、构建、git、只读查询。
- 默认 **UTF-8 无 BOM**（含中文）。

**阶段门禁**

| 用户说 | Route | 禁止（未获继续指令前） |
| --- | --- | --- |
| 写方案 / 出方案 / 设计 | `brainstorming` | 改业务代码、写 plan、派子 Agent |
| 写计划 / 实施计划 | `writing-plans` | 同上 |
| 开始实现 / 直接做 / 并行执行 | 已过门禁后实现 | — |
| 写计划然后执行 / 出方案并直接做 | **仅** writing-plans 或 brainstorming | 同轮禁止实现 |

- **同轮禁止：** Write 了 `specs/` / `plans/` / `decisions/` → **结束本轮**；不得同轮改业务代码。
- **实现前置：** 用户**单独**说「开始实现 / 直接做 / 并行执行」；或 spec/plan `approved: true`；或 Tier 0 / Tier 1。
- **Tier 1 完成：** 须 Write `.ai-runtime-artifacts/verifications/*-verification-lite.md`。
- **暂停回复须含：** 产物路径、摘要、`## Next` 选项。

## 每任务（必做）

1. 首行：`「Harness：<route 或 "Tier 0 小改动" | "Tier 1 Leader 直做">」`
2. 次行（stage skill / Tier 1+）：`Skills: <slug>@<path> loaded|skipped`
3. **沟通语言：** 对用户回复与子 Agent 派发/整合使用**中文**
4. **非 Tier 0**：Read `routing.md` 按 § 追加加载

## 按 routing 判定加载（勿在会话开始预读）

| 判定 | 再读（按序） |
| --- | --- |
| 设计 / spec | `brainstorming` skill → `core/artifacts.md` |
| 计划 | `writing-plans` skill → `artifacts.md` → `artifact-templates/plan.harness-overlay.md` |
| 验证 / 跑命令 | `verification-before-completion` → `project.verification.md` |
| 多 task / 已批准 plan + 委派 | `orchestration` → `core/orchestration/dispatcher-workflow.md` |
| Leader 直做 / Tier 1 | `verification-before-completion` → Write `verification-lite.md` |
| Git | `git-xywh` + `project.git.md` |
| 改代码 / 验证（实现阶段） | `project.profile.md`、`context-map.md`（涉及模块时） |

## 委派

Trae Agent 模式下，通过 `.agents/agents/<role>.md` 共享 subagent 委派。角色映射见 `platform/trae/bindings.md`。

## 禁止

- 未过阶段门禁修改业务代码
- 实现与审查同一 subagent 实例
- 跳过尾盘集体测试或集体审查
- Shell 写/改仓库文本文件（须用 Write）
- **把产物写到 `.ai-runtime-artifacts/` 以外的位置**（spec/plan/verification/review/execution-log 等必须写入对应子目录）
- 把 plan 写到平台私有目录
- 用 `docs/superpowers/` 代替 `.ai-runtime-artifacts/`

## 产物落盘目录（强制）

| 产物类型 | 目录 |
| --- | --- |
| spec / 方案 | `.ai-runtime-artifacts/specs/` |
| plan / 计划 | `.ai-runtime-artifacts/plans/` |
| dispatch / 调度 | `.ai-runtime-artifacts/plans/`（同 stem 的 `*-dispatch.md`） |
| verification / 验证 | `.ai-runtime-artifacts/verifications/` |
| collective-test / 集体测试 | `.ai-runtime-artifacts/verifications/*-collective-test.md` |
| review / 审查 | `.ai-runtime-artifacts/reviews/` |
| code-review / 代码审查 | `.ai-runtime-artifacts/reviews/*-code-review.md` |
| execution-log / 执行日志 | `.ai-runtime-artifacts/execution-logs/` |
| dispatch-track / 追踪 | `.ai-runtime-artifacts/execution-logs/tracking/` |
| decision / 决策 | `.ai-runtime-artifacts/decisions/` |
| retro / 复盘 | `.ai-runtime-artifacts/retros/` |
| research / 调研 | `.ai-runtime-artifacts/research/` |

**例外：** harness-kit 仓库自身（`.gitignore` 排除 `.ai-runtime-artifacts/`）的 closeout 示例可放 `docs/runtime/closeouts/`。
