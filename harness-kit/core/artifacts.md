# Artifact Contract

## 目录

AI 过程产物统一放在项目根目录 `.ai-runtime-artifacts/`：

| 目录 | 用途 |
| --- | --- |
| `.ai-runtime-artifacts/specs/` | 需求理解、方案设计、设计说明 |
| `.ai-runtime-artifacts/plans/` | 实施计划、任务拆解 |
| `.ai-runtime-artifacts/reviews/` | 代码审查（`*-code-review.md`）、文档审查（`*-document-review.md`） |
| `.ai-runtime-artifacts/verifications/` | 验证报告、**集体测试**（`*-collective-test.md`）、doctor 摘要 |
| `.ai-runtime-artifacts/decisions/` | 架构决策、技术取舍 |
| `.ai-runtime-artifacts/retros/` | 复盘、阶段总结 |
| `.ai-runtime-artifacts/research/` | 网探调研报告、截图取证（`research/screenshots/`） |
| `.ai-runtime-artifacts/execution-logs/` | 执行日志、HANDOFF、并行编排摘要 |
| `.ai-runtime-artifacts/execution-logs/tracking/` | DISPATCH 逐步追踪（append-only） |

## 文件命名

```text
YYYY-MM-DD-<topic>-<artifact>.md
```

示例：

```text
2026-05-14-ai-agent-harness-spec.md
2026-05-14-ai-agent-harness-plan.md
2026-05-14-ai-agent-harness-verification.md
2026-05-28-auth-batch-collective-test.md
2026-05-28-auth-batch-code-review.md
2026-05-26-react-19-research-report.md
```

**尾盘命名约定：**

| 后缀 | 目录 | 模板 |
| --- | --- | --- |
| `-collective-test.md` | `verifications/` | `artifact-templates/collective-test.md` |
| `-code-review.md` | `reviews/` | `artifact-templates/code-review.md` |
| `-document-review.md` | `reviews/` | `artifact-templates/document-review.md` |

## Front Matter

每个过程产物必须以 YAML front matter 开头：

```yaml
---
artifact: implementation-plan
route: superpowers:brainstorming -> superpowers:writing-plans
skills:
  - brainstorming
  - writing-plans
skills_evidence:
  - brainstorming/SKILL.md（路径见适配器 bindings）
source:
  - AGENTS.md
  - harness-kit/core/routing.md
created_at: 2026-05-14
---
```

必填字段：

| 字段 | 说明 |
| --- | --- |
| `artifact` | 产物类型 |
| `route` | 本次任务经过的路由 |
| `skills` | 实际使用的 skill slug；route 含阶段 skill 时**禁止空** |
| `skills_evidence` | P0 可选（overlay 有示例）；**P1 起** route 含 stage skill 时**必填**至少一条 path 或 `skipped: <slug> (not found)` |
| `dispatch` | 仅 `implementation-plan`：指向同 stem 的 `*-dispatch.md`；单 WU 可 `n/a` |
| `source` | 产物依据的入口、规则、需求或上下文 |
| `created_at` | 创建日期，格式 `YYYY-MM-DD` |
| `tier` | 可选；Tier 1 轻量验证产物填 `1` |

## 任务 Tier 与产物（摘要）

| Tier | 产物 | 模板 |
| --- | --- | --- |
| 0 | 无 FM | — |
| 1 | `verifications/*-verification-lite.md` | `verification-lite.md` |
| 2+ | spec/plan/dispatch、execution-log、collective-test、code-review 等 | 各 `artifact-templates/` |

细则：`core/routing.md` § 任务 Tier、§ WU 编排硬触发。

## Artifact 类型

- `spec`
- `implementation-plan`
- `implementation-dispatch`
- `review`
- `verification`
- `verification-lite`
- `execution-log`
- `dispatch-track`
- `handoff`
- `progress-summary`
- `wu-checklist`
- `decision-record`
- `retro`
- `research-report`
- `article`
- `runbook`
- `project-profile`
- `context-map`

## Skill 产物 vs Harness 模板

| 类型 | 正文从哪来 | Harness 提供 |
| --- | --- | --- |
| spec（`brainstorming`） | **SKILL.md** 流程与结构 | `spec.harness-overlay.md`（FM + `## Next`） |
| plan（`writing-plans`） | **SKILL.md**（Task 细步等） | `plan.harness-overlay.md`；并行时 `dispatch.harness-overlay.md` |
| verification 等 stage skill | skill 纪律 + 简短记录 | `verification.md`、`verification-lite.md`（Tier 1）、`collective-test.md` |
| 尾盘集体审查 | Reviewer 返回 + Leader 落盘 | `code-review.md` |
| execution-log、track、handoff、wu-checklist 等 | **artifact-templates/** 全文 | 无对应 stage skill |

**路径覆盖：** 接入 Harness 的项目，brainstorming / writing-plans 产物写入 `.ai-runtime-artifacts/`，不默认写入 `docs/superpowers/`（除非用户要求双份）。

**禁止：** 用 `artifact-templates/spec.md` / `plan.md` 短提纲代替 skill 正文（二者已为 redirect stub）。

**plan + dispatch 命名：** `YYYY-MM-DD-<topic>-plan.md` 与 `YYYY-MM-DD-<topic>-dispatch.md` 同 stem；plan FM 含 `dispatch:` 指针。

## 规则

- 过程产物必须写清 route 和 skills（有阶段 skill 时 `skills` 非空，与 route 一致）。
- 如果用户指定了额外 skills，route 和 skills 必须同时包含默认 route 与用户指定 skills。
- 如果跳过默认 skills，source 或正文必须记录用户明确要求跳过的原因。
- 过程产物必须写清 source 和 created_at。
- 验证类产物必须写清命令、结果和未验证项。
- 架构决策必须写清接受方案、拒绝方案和原因。
- 不在过程产物里记录 secret 或 provider 配置。

## 参考资料索引

**检查清单已内嵌到各 Agent 定义文件中**，无需外部引用。各 Agent 的 `.md` 文件包含完整的检查表。

