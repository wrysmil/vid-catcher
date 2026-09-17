# Continuous Loop（Claude Code，HANDOFF 驱动）

Claude Code 平台**没有**原生 continuous loop，长期自治用 **HANDOFF + DISPATCH-TRACK** 串联多会话。与 Cursor 不同：Cursor 走 `continuous_mode` 会话内循环，Claude 走「写 HANDOFF → 新会话读 HANDOFF + DISPATCH-TRACK 续跑」。

---

## 物理能力诚实声明

Claude 平台的「leader + sub-agent 编排」是 **Leader 流程 + 钩子提示 + 文件契约** 的组合，**不存在** 调度器/状态机/自动触发器。

**关键后果：**

- Leader 在 Claude Code 会话里看到的**只是根 CLAUDE.md + AGENTS.md**；整本 `core/orchestration/*` 文档要 Leader **主动 Read**
- "完成 ≠ 末个 WU 返回"、"未生成产物不能声称完成"、"WORKTREE-CLOSE" 等规范文本，**都是 Leader 自律，不是平台门禁**
- `collective-test` / `code-review` 产物**不会**在 WU 返回时自动生成——Leader 必须手动走 A 集体测试 → B 集体审查 → C 关闭
- "下一周期"完全靠**人工**新开会话并读 HANDOFF，不是 agent 自己续命

需要硬门禁的功能（如阻断 EnterPlanMode）必须在 `CLAUDE.md` / `AGENTS.md` 中显式写规则。

---

## 模式对比

| loop_mode | 含义 | 适用 |
| --- | --- | --- |
| `single-pass` | 单会话完成一个可交付单元 | **默认**；日常功能开发 |
| `maintenance` | 仅 bugfix / 安全 / 依赖 | 无新 feature 阶段 |
| `continuous` | 多周期自治循环 | 需人工监督 + 明确 opt-in |

**禁止**在未 sandbox 验证前将 `continuous` 设为默认。

---

## 周期阶段（Claude）

每个 **cycle** 跨**多次会话**，每会话对应一个可交付子集：

| 阶段 | Leader 动作 | 产物 |
| --- | --- | --- |
| 0 初始化 | 新会话首句：读 `HANDOFF.md` + `DISPATCH-TRACK-*.md` 末段 | 状态恢复 |
| 1 需求/设计 | Load **`brainstorming`** → spec | `specs/` |
| 2 计划 | Load **`writing-plans`** | `plans/` |
| 3 实现 | Load **`orchestration`** → dispatcher | `execution-logs/` + 代码 |
| 4 验证 | Load **`verification-before-completion`** → reviewer Task | `verifications/` + `reviews/` |
| 5 反思 | Leader 摘要 | `retros/` |
| **6 接力（HANDOFF）** | Leader 写 `HANDOFF.md` 末段 `## Next` | `HANDOFF.md` |
| 7 收工 | 关闭当前会话 | — |
| 8 续跑（下次会话） | 步骤 0 | — |

---

## HANDOFF 协议

**写时机：**

- 本 cycle 所有 WU 返回后、集体测试 PASS 前，**不**写 HANDOFF（避免半成品接力）
- 集体测试 + 集体审查都通过、execution-log 关闭后 → **必须**写 HANDOFF
- 用户明确说「暂停」「明天继续」 → 立即写 HANDOFF
- 上下文预算 >80% → 主动写 HANDOFF

**写什么**（按 `artifact-templates/handoff.md` 模板）：

- 周期 ID、阶段、当前 GROUP/WU 状态、阻塞、`## Next`（3–5 步可执行）
- 不复制 plan 全文，只**链接**到 `DISPATCH-TRACK-*.md` 末行

**DISPATCH-TRACK 协同：**

- HANDOFF 是给**人**看的导航；TRACK 是给**机器**执行的状态（单一真相源）
- 计划勾选、WU 状态变更**全部** append-only 写到 TRACK

---

## 续跑流程

新会话首句建议：

```text
Harness：continuous-loop (claude) — 接续 HANDOFF
读：.ai-runtime-artifacts/execution-logs/HANDOFF.md
读：.ai-runtime-artifacts/execution-logs/tracking/DISPATCH-TRACK-<date>-<topic>.md
按 HANDOFF `## Next` 继续
```

Leader 动作：

1. 读 `HANDOFF.md` → 取周期 ID、阶段、`## Next`
2. 读 `DISPATCH-TRACK-*.md` 末段 → 确认 WU 实际状态
3. 比对：HANDOFF 描述 vs TRACK 实际 → 不一致先与用户对账
4. 按 `## Next` 执行第一步；执行完**append**到 TRACK，**不**改 HANDOFF

---

## 启用 continuous 前检查清单

- [ ] 至少完成 2 次 clean single-pass cycle
- [ ] `feature` 分支工作，main 受保护
- [ ] `handoff.md` + `progress.md` 模板已使用熟练
- [ ] 人工门禁：plan 批准、PR 审查（无 auto-merge）

---

## 禁止

- 未 opt-in 默认 continuous
- continuous 模式下跳过 verification / collective-review
- 同一 Task 既实现又审查
- 写 HANDOFF 不 append TRACK（或反之）
- 跨会话「凭印象」继续，不读 HANDOFF / TRACK
- HANDOFF `## Next` 留空或写「按需继续」（不可执行）
