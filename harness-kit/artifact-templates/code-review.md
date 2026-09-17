---
artifact: review
route: orchestration:dispatcher-workflow -> batch-closeout
skills:
  - requesting-code-review
  - orchestration
skills_evidence:
  - .agents/skills/requesting-code-review/SKILL.md
  - .agents/skills/orchestration/SKILL.md
source:
  - .ai-runtime-artifacts/plans/<YYYY-MM-DD>-<topic>-plan.md
  - docs/superpowers/specs/2026-05-28-batch-closeout-review-and-collective-test.md
created_at: <YYYY-MM-DD>
batch_id: GROUP-1
worktree_id: 
worktree_path: 
reviewer_instance: reviewer
verdict: APPROVE
---

# <Topic> 集体代码审查

> **写入者：** Leader（收到 `reviewer` 返回后落盘）。Reviewer 为 readonly，不 Write 本文件。

## 防跳过提醒

| 合理化借口 | 现实 |
|-----------|------|
| "改动不大，审查可以轻一点" | 小改动可能引入全局影响。边界的代码最危险 |
| "时间紧，快速过一下" | 匆忙通过的审查等于没审查 |
| "都是自己人写的，放心" | 信任 ≠ 不审查。审查是为了质量，不是怀疑 |
| "这个 WU skip_reviewer_eligible" | 只有满足所有跳过条件的小 WU 才能跳过，不是 Leader 说了算 |

## 审查范围

- 文件列表或 `git diff <BASE>..<HEAD>` 摘要：
- BASE_SHA / HEAD_SHA：

## 变更尺寸评估

| 指标 | 值 | 判定 |
|------|----|------|
| 变更行数 | | ≤100 理想 / ≤300 可接受 / 1000+ 必须拆分 |
| 变更文件数 | | ≤5 理想 / ≤10 可接受 / 20+ 必须拆分 |

> 超过 ~300 行时，主动建议拆分为多个可独立审查的 WU。

## 对照依据

- spec：
- plan：
- done criteria 勾选：

## Findings

### Critical

- 无 |

### Important

- 无 |

### Suggestion

- 无 |

### Nit

- 无 |

## 结构疗法建议（可选）

| 重构模式 | 适用场景 | 建议 |
|---------|---------|------|
| 提取方法/函数 | 长方法、职责混合 | 将逻辑块提取为命名良好的函数 |
| 替换条件式为多态 | 复杂 if-else / switch 链 | 用策略模式或多态替代 |
| 分离编排与逻辑 | 一个函数同时做调度和计算 | 把纯逻辑抽到独立纯函数中 |
| 折叠继承体系 | 过度设计的抽象层次 | 合并回单一实现，等第三次使用时再抽象 |

## 死代码 / 孤儿代码检查

- [ ] 重构后是否存在无引用的函数/类型/文件
- [ ] 是否存在注释掉的代码块未清理
- [ ] 旧实现是否已完全移除（而非仅标记 deprecated）

## 证据

- Reviewer 已读/已跑：

## 未验证项

- 无 |

## 结论

**verdict:** APPROVE | BLOCK | SKIPPED

（若 SKIPPED：写明 `docs/superpowers/specs/2026-05-26-coder-role-design.md` § 小 WU 跳过 Reviewer 全条件 + 各 WU `skip_reviewer_eligible`）

## Next

- APPROVE → 可合并/提测；更新 execution-log
- BLOCK → 开 `review-fix` WU，修复后重跑集体测试（步骤 A）再审查
- SKIPPED → 记录跳过依据；仍须 collective-test PASS
