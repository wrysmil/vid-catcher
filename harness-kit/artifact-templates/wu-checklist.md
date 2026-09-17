---
artifact: wu-checklist
route: cursor-orchestration:dispatcher-workflow
skills:
  - cursor-orchestration
source:
  - .ai-runtime-artifacts/plans/<plan-file>.md
created_at: YYYY-MM-DD
platform: cursor
wu_id: WU-<id>
wu_type: feature
wu_skills: []
agent_role: coder
---

# CHECKLIST — <topic> / WU-<id>

Coder 或 Implementer 在**本文件**（及 plan）里把 `- [ ]` 改为 `- [√]`；Reviewer 对照验收。禁止仅在 Agent 回复里复述 `[√]`。

`wu_skills`：Leader 写入本 WU 建议加载的 skill slug 列表；空数组表示不加载 skill。`agent_role`：`coder` | `implementer`。

## Done criteria

- [ ] 
- [ ] 

## 允许修改

- 

## 验证命令

- [ ] 

## 开发者自检（仅 Coder）

- [ ] Done criteria 逐项满足
- [ ] 错误路径与日志符合项目规范
- [ ] 单测已更新且通过（或已声明 test_exempt）
- [ ] verification 命令已运行

- self_check: PASS | FAIL
- open_items: 无 | ...
- skip_reviewer_eligible: yes | no

## 完成签名

- Worker 完成时间: 
- agent_role: coder | implementer
- Reviewer 结论: APPROVE | BLOCK | skipped（小 WU）
