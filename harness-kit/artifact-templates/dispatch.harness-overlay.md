---
artifact: implementation-dispatch
route: orchestration:dispatcher-workflow
plan: .ai-runtime-artifacts/plans/YYYY-MM-DD-<topic>-plan.md
skills:
  - writing-plans
  - orchestration
skills_evidence:
  - ~/.agents/skills/writing-plans/SKILL.md
source:
  - core/orchestration/dispatcher-workflow.md
created_at: <YYYY-MM-DD>
---

# <Topic> — Harness 执行图

> 实施步骤以 **plan** 为准；本文件只描述并行 GROUP / WU 与派发。多轮审阅时优先改本文件，避免扰动 plan 内 Task 细步。

## 执行图

```markdown
GROUP-1:
  WU-01: … | 标题: <wu_title_zh> | 文件: … | 依赖: 无 | wu_type: feature | agent_role: coder|implementer|test-engineer | workspace_scope: wu|none | worktree_path: <path or n/a> | branch: <branch or n/a> | wu_skills: auto
```

## 变更记录（可选）

| 轮次 | 日期 | 变更摘要 |
| --- | --- | --- |
| 1 | | 初稿 |

## Next

- 执行图确认 → 说「开始实现」或「并行执行」
- 只改 plan 任务、不改并行策略 → 仅改 `*-plan.md`
- 只改 WU 拆分 / 依赖 → 改本文件并告知 Leader 审阅
