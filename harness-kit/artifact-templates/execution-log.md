---
artifact: execution-log
route: orchestration:dispatcher-workflow
skills:
  - orchestration
source:
  - <对应的 spec 或 plan 路径>
created_at: <YYYY-MM-DD>
worktree:
  id: 
  path: 
  branch: 
  base_ref: 
  head_ref: 
---

# <Topic> Execution Log

## 实际路由

<声明实际使用的工作流：orchestration:dispatcher-workflow / 直接编码 / ...>

## 变更文件

- `path/to/file` — 变更说明

## 执行摘要

<1-3 句话说明做了什么>

## 尾盘门禁

| 门禁 | 产物 | 结论 |
| --- | --- | --- |
| 集体测试 | `verifications/YYYY-MM-DD-<topic>-collective-test.md` | PASS / FAIL |
| 集体审查 | `reviews/YYYY-MM-DD-<topic>-code-review.md` | APPROVE / BLOCK / SKIPPED |

**批次完成条件：** 上表两项均已落盘且结论合格；未满足不得写「本 GROUP / 本批次交付完成」。细则见 `docs/superpowers/specs/2026-05-28-batch-closeout-review-and-collective-test.md`。

## 测试摘要

<1–3 句或链接 collective-test 产物>

## 审查摘要

<1–3 句或链接 code-review 产物>

## 待验证

- <列出需要验证的点；尾盘 A/B 通过后可为空>

## Next

- 尾盘未做 → Leader 执行集体测试 + 集体审查并落盘
- 发现问题需要修复 → 描述问题
- 尾盘通过 → 说「完成」或进入 Git（`git-xywh`）
