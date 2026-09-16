---
name: requesting-code-review
description: Harness 代码审查：WU 轻量审查与 GROUP 尾盘集体审查。完成实现、批次收尾、合并前使用。触发：review、审查、code-review、集体审查。
---

# Requesting Code Review（Harness）

**Core principle:** Review early, review often — **Harness 下必须用独立 `reviewer` 实例，禁止裸 `generalPurpose`。**

## 两层审查（必辨）

| 层 | 谁发起 | 机制 | 落盘 |
| --- | --- | --- | --- |
| **WU 轻量审查** | Coder（WU 内） | 独立 `reviewer` 实例 | **不落盘**；返回 `code_review: PASS\|BLOCK` |
| **GROUP 集体审查** | Leader（尾盘 B） | 独立 `reviewer`；须先 collective-test PASS | Leader Write `reviews/*-code-review.md` |

**顺序（尾盘）：** collective-test → 本 skill → code-review 产物。细则：batch-closeout spec §4。

## 委派协议

1. 声明 `Skills: requesting-code-review@<path> loaded`
2. Load 本 skill
3. 委派 **独立 `reviewer` 实例**（与所有 Coder/Implementer **不同实例**；readonly）
4. Prompt 正文：`.agents/agents/reviewer.md`；占位符见 `code-reviewer.md`
5. **Leader** 将集体审查返回 Write `artifact-templates/code-review.md` 路径；Reviewer **不** Write 文件

**平台绑定：** 见 `platform/*/bindings.md`（SpawnWorker(reviewer)）。

**范围证据：** 优先 **文件列表 + diff 摘要**；worktree 批次可用 `{BASE_SHA}`/`{HEAD_SHA}`，非必须。

## 何时必须

- GROUP 尾盘（Tier 2+ 批次交付）
- WU 内 Coder 闭环（`coder.md` § 轻量审查）
- 合并 main 前（Leader 组织）

## 禁止

- 实现与审查同一 subagent 实例
- 无 `reviewer` 约束的 Task
- 跳过 collective-test 直接集体审查
- Reviewer 会话内 Write `.ai-runtime-artifacts/`
- 仅以 Coder `code_review: PASS` 替代尾盘集体审查

## 反馈处理

- Critical → 立即修；Important → 继续前修；Minor → 记录
- 有依据时可 push back

## Superpowers 原版（非 Harness 项目）

无 Harness Kit 时，可用 Task `general-purpose` + git SHA + `code-reviewer.md` 模板（见 skill 副本 `_vendor` 说明）。**本项目忽略该路径。**
