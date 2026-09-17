---
artifact: handoff
route: orchestration:dispatcher-workflow
skills:
  - orchestration
source:
  - core/orchestration/tracking/schema.md
created_at: YYYY-MM-DD
platform: cursor
---

# HANDOFF — <topic>

> 覆盖写。新会话 / 新 Task 启动前读取本文件恢复。

## 中断点

- 最后完成 WU: 
- 当前 GROUP: 
- 下一步: 

## 已做决策

- 

## 待完成 WU

| WU | 状态 | 文件 | 阻塞 |
| --- | --- | --- | --- |
| WU-01 | completed | | |
| WU-02 | in_progress | | |

## Git 沙箱

- worktree_id: 
- worktree_path: 
- branch: 
- base_ref: 

## 关键文件

- plan: 
- dispatch: 
- track: `.ai-runtime-artifacts/execution-logs/tracking/DISPATCH-TRACK-*.md`

## 验证状态

- 已跑: 
- 未跑: 

## 给下一个 Agent 的指令

```text
从 HANDOFF 恢复，继续 <具体步骤>。
```
