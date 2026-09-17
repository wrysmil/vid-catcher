---
artifact: spec
route: superpowers:brainstorming
skills:
  - brainstorming
skills_evidence:
  - ~/.agents/skills/brainstorming/SKILL.md
source:
  - AGENTS.md
  - core/routing.md
created_at: <YYYY-MM-DD>
status: draft
approved: false
---

# Harness overlay（非正文模板）

> **正文：** 按已 Load 的 **brainstorming** skill 撰写（含方案对比、设计节、Spec 自检等）。
> **禁止**用 `artifact-templates/spec.md` 历史短提纲替代 skill 流程。
> **路径：** `.ai-runtime-artifacts/specs/YYYY-MM-DD-<topic>-spec.md`（覆盖 skill 默认 `docs/superpowers/specs/`）。

## Next

**（写入后须暂停，等用户明确继续 — 见 `harness-kit/core/routing.md` § 阶段门禁）**

- 确认方案无误 → 说「写计划」或「制定实施计划」
- 变更范围小、无需计划 → 说「直接实现」或「直接做」
- 需要调整方案 → 直接说修改意见
