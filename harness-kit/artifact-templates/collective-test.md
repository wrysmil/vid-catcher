---
artifact: verification
route: orchestration:dispatcher-workflow -> batch-closeout
skills:
  - verification-before-completion
skills_evidence:
  - .agents/skills/verification-before-completion/SKILL.md
source:
  - project.verification.md
  - docs/superpowers/specs/2026-05-28-batch-closeout-review-and-collective-test.md
created_at: <YYYY-MM-DD>
batch_id: GROUP-1
worktree_id: 
worktree_path: 
verdict: PASS
---

# <Topic> 集体测试

> **纪律：** 先 Load **verification-before-completion**；**先跑命令、再给结论**（禁止「应该通过」）。  
> **写入者：** Leader。WU 内 Coder 单测摘要可引用，**不能替代**本表命令的本机重跑。

## 防跳过提醒

| 合理化借口 | 现实 |
|-----------|------|
| "每个 WU 都跑过单测了，不用重跑" | 单测隔离 ≠ 集成正常。WU 间交互可能引入隐性冲突 |
| "改动很小，批次测试太重型" | 批次越小，交互 bug 越隐蔽。不跑就是赌 |
| "时间不够了，直接审查吧" | 没跑过测试的审查是浪费审查者的时间 |
| "Coder 说都通过了" | Coder 说的是它的上下文，Leader 必须在本机验证 |

## 变更范围

- 本批次触及模块/目录：

## WU 已覆盖项（引用，非替代）

| WU | 命令/结论摘要 |
| --- | --- |
| WU-01 | |

## 命令表

| 命令 | cwd | exit | 关键输出摘要 |
| --- | --- | --- | --- |
| | | 0 | |

## 集成 / E2E

- 无 | Test Engineer WU-id + 摘要：

## 未验证项

- 无 |

## 残留风险

- 无 |

## 结论

**verdict:** PASS | FAIL

## Next

- PASS → 进入集体代码审查（`artifact-templates/code-review.md`）
- FAIL → 开 bugfix WU；不得进入审查或声称批次完成
