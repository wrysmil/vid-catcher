---
artifact: implementation-dispatch
route: orchestration:dispatcher-workflow
plan: .ai-runtime-artifacts/plans/2026-09-19-summarize-export-polish-plan.md
skills:
  - orchestration
skills_evidence:
  - harness-kit/.agents/skills/orchestration/SKILL.md
source:
  - harness-kit/core/orchestration/dispatcher-workflow.md
  - .ai-runtime-artifacts/contracts/2026-09-19-contract-summarize-sse.md
created_at: 2026-09-19
---

# 总结面板排版与导出 — 执行图

> 实施步骤以 plan 为准。用户已说「开始实现」+「可以并行执行」。

## 执行图

GROUP-1（并行）:

- WU-01: 后端 SSE JSON 编码 | 标题: 总结流 token 编码 | 文件: `backend/app/api_summarize.py`, `backend/tests/test_api_summarize.py` | 依赖: 无 | wu_type: feature | agent_role: coder | workspace_scope: wu | worktree_path: `/Users/mima0000/Documents/学习-001/do-project/.harness-worktrees/vid-catcher/wt-2026-09-19-summarize-export-polish` | branch: `harness/wt-2026-09-19-summarize-export-polish` | wu_skills: source-driven-development, incremental-implementation, test-driven-development, verification-before-completion
- WU-02: 前端解析 / 排版 / 导出 | 标题: 总结面板导出与排版 | 文件: `frontend/src/api/summarize.js`, `frontend/src/utils/subtitleFormat.js`, `frontend/src/utils/mindmapExport.js`, `frontend/src/components/VideoSummary.vue`, `docs/需求文档.md` | 依赖: 无（契约已定） | wu_type: ui | agent_role: coder | workspace_scope: wu | worktree_path: 同上 | branch: 同上 | wu_skills: source-driven-development, incremental-implementation, frontend-ui-engineering, verification-before-completion

## 变更记录

| 轮次 | 日期 | 变更摘要 |
| --- | --- | --- |
| 1 | 2026-09-19 | 初稿：后端 / 前端文件不相交，共享 worktree |

## Next

- 派发后等 WU 返回 → Leader 集体测试 + 审查
