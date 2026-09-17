---
artifact: dispatch-track
route: orchestration:dispatcher-workflow
skills:
  - orchestration
source:
  - core/orchestration/tracking/schema.md
  - .ai-runtime-artifacts/plans/<plan-file>.md
created_at: YYYY-MM-DD
platform: cursor
topic: <topic>
---

# DISPATCH-TRACK — <topic>

Leader 维护。条目 **append-only**。

## 执行图

（从 plan 复制或链接 `*-dispatch.md`）

## Git 沙箱

- worktree_id: 
- worktree_path: 
- branch: 
- base_ref: 

## 日志

<!-- 在此追加条目，格式见 tracking/schema.md -->

```text
[YYYY-MM-DD HH:MM] DISPATCH-INIT | Leader | Status: started
Detail: 创建 track，plan=<path>
Sub-agents: 0
Output: none
Next: WORKTREE-INIT
```

```text
[YYYY-MM-DD HH:MM] WU-02-worktree | Leader | Status: started
Detail: 创建 WU-02 worktree（<wu_title_zh>）
Output: .worktrees/<...>
Next: 派发 WU-02（worktree_path=<...> branch=<...>）
```
