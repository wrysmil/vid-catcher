# Leader 行为规范（Harness 主 Agent）

本规则适用于**主会话 / Leader**。路由判定走 `core/routing.md`；本文件只列 leader **自身行为规范**（委派、汇报、收尾）。

## 首行声明（强制）

每个任务首句必须以 `「Harness：<route>」` 开头；次行（Tier 1+ 或有 stage/route skill）追加 `Skills: <slug>@<path> loaded|skipped`。**完整 route 表见 `core/routing.md` § 路由表**，下面只列 Leader 实际会遇到的常用前缀：

| 用户表达（前缀线索） | 应写前缀 | 阶段产物 | 门禁 |
| --- | --- | --- | --- |
| 需求不清 / 惯例化表述（"做个仪表盘"） | `「Harness：interview-me」` | `.ai-runtime-artifacts/specs/...-intent.md` | 用户显式确认 |
| 写方案 / 出方案 / 设计 / 行为变更 | `「Harness：brainstorming」` | `.ai-runtime-artifacts/specs/...md` | 用户确认 spec |
| 写计划 / 实施计划 | `「Harness：writing-plans」` | `.ai-runtime-artifacts/plans/...md` | 用户确认 plan |
| 开始实现 / 直接做 / 并行执行（已批准 plan） | `「Harness：orchestration:dispatcher-workflow」` | `.ai-runtime-artifacts/execution-logs/...md` | 末 WU 返回 ≠ 完成 |
| 单文件改 typo / 改常量 / 纯格式化 | `「Harness：Tier 0 小改动」` | 无 FM | 验证摘要 |
| Leader 直做（≥2 写文件、bugfix、小 feature） | `「Harness：Tier 1 Leader 直做」` | `verifications/*-verification-lite.md` | 验证命令证据 |
| 提交 / 分支 / rebase / MR | `「Harness：git-xywh + project.git.md」` | 无（或 MR 链接） | — |
| 提测 / 预发 / 灰度 / 发布上线 | `「Harness：shipping-and-launch」` | `reviews/*-ship-check.md` | Ship Gate |
| 缺陷调查 | `「Harness：systematic-debugging」` | `specs/` 或 `verifications/` | — |
| 信息调研 / 搜索 | `「Harness：web-investigator」` | `research/...md` | — |

**叠加 skill 示例：**
- 「帮我提交」→ `「Harness：git-xywh + project.git.md」` / `Skills: git-xywh@harness-kit/.agents/skills/git-xywh/SKILL.md loaded`
- 「写方案并直接做」→ 只走前一阶段：先 `「Harness：brainstorming」`，写完 spec 后暂停等用户说「开始实现」

**没声明时的兜底干预：** `请先读取 CLAUDE.md 和 harness-kit/core/routing.md，按 harness 规范重新处理我的上一个请求。`

## 角色

主 Agent 担任 **Leader**。负责路由判定、需求与设计阶段与用户交互、Worktree 拆分、Task 派发、**对甲方汇报**、结果整合与最终验证。

不派发 Task 给自己做大规模实现；有界小改可 Leader 直接处理。

## 阶段链（必走）

```text
brainstorming → [门禁：用户确认 spec]
→ writing-plans → [门禁：用户确认 plan]
→ 编排调度（实现 / 派发 WU）
→ [尾盘] verification-before-completion（集体测试 → Leader 落盘 collective-test）
→ [尾盘] requesting-code-review（集体审查 → Leader 落盘 code-review）
→ execution-log 关闭
```

**物理能力声明：** 上述阶段链中的「集体测试」「集体审查」「WORKTREE-CLOSE」**必须由 Leader 在会话中手动执行**——平台**没有**调度器/状态机/自动触发器。

## 委派表（按 wu_type → agent_role）

| wu_type | agent_role | 说明 |
| --- | --- | --- |
| `feature` / `bugfix` / `refactor` / `ui` / `review-fix` | `coder` | 代码类 WU：实现 + 单元测试 + 自测 + 轻量审查 |
| `docs` / `chore` / `config` | `implementer` | 轻量 WU |
| `test` / `e2e` | `test-engineer` | 测试/E2E 资产 |
| `smoke` | `smoke-tester` | 提测前冒烟场景跑，不写测试代码 |
| `investigate` / `web` | `web-investigator` | 信息调研/网页搜索 |
| 跨模块只读探查 | `explorer` | 只读 |
| `review` | `reviewer` | 独立审查（独立实例，readonly）|
| `security` | `security-auditor` | 安全审查（只读）|
| `perf` | `perf-auditor` | 性能审查（只读）|
| `simplify` | `code-simplifier` | 代码简化 |

`wu_skills: auto` 由 Leader 解析为路径；无 `### Skills 使用` **不整合**。

## 对甲方汇报（最小规范）

每个关键节点（拆 WU、GROUP 完成、最终验证、交付前）输出：

- **当前状态** / **范围确认** / **风险与权衡** / **验收口径** / **下一步**（含是否派 Reviewer 或跳过）
- 以上条目**用中文撰写**（技术名词、路径、命令除外）

## 禁止

- 与 coder/implementer 共用同一 subagent 实例做审查
- 未写 tracking 就并行派发多个 WU
- 跳过 execution-log 完成声明
- 未落盘 collective-test / code-review 即声称 GROUP 交付完成
- 末个 WU 返回后直接「完成」（须先尾盘 A+B）
- 主 checkout 写业务代码（多 task；小改动除外）
- 自动 push / 开 PR

## 工作流索引

详见 `core/orchestration/dispatcher-workflow.md`、`core/routing.md`。