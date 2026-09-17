---
artifact: verification-lite
route: leader-direct | 小改动直做
skills:
  - verification-before-completion
skills_evidence:
  - ~/.agents/skills/verification-before-completion/SKILL.md
source:
  - <用户原话或 issue 摘要>
created_at: <YYYY-MM-DD>
tier: 1
---

# <Topic> — 轻量验证（Tier 1）

> **适用：** Leader 直做简单任务（≥2 写文件 / 跑测试 / fix·实现类），**不**走 spec/plan/WU 编排。
> **纪律：** Load `verification-before-completion`；先跑命令再给结论。

## 防跳过提醒

| 合理化借口 | 现实 |
|-----------|------|
| "只改了一行，不用验证" | 一行改动能破坏整个构建 |
| "上次跑过了" | 代码变了，上次不等于这次 |
| "看起来没问题" | 看起来 ≠ 验证过 |
| "太简单了，省掉吧" | 简单的变更最容易被忽略，引起的回归最难查 |
| "时间紧，跳过这次" | 跳过验证省的 2 分钟，将来 debugging 要花 2 小时 |

## 范围

- 改动文件：
- 路由判定：Tier 1（Leader 直做）

## 命令与结果

| 命令 | 结果 |
| --- | --- |
| | |

## 未验证项

- 无 | …

## Next

- 任务完成 → 无需暂停（除非用户要求 commit/MR）
- 范围扩大 → 补 spec/plan 或升级 Tier 2 编排
