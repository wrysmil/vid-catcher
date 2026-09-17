# Trae 子 Agent 路由与委派协议

## 规范优先级

1. `harness-kit/core/routing.md` — 路由、阶段门禁、按判定加载（强制）
2. `.trae/rules/ai-entry.md` § 文件写入与阶段门禁（强制）
3. 本文件 — Trae 委派映射
4. 根目录 `AGENTS.md` — Harness 覆盖层

平台映射：`platform/trae/bindings.md`。

## Harness 强制声明

收到任务后，第一句必须为：

```text
「Harness：<route 或 "Tier 0 小改动" | "Tier 1 Leader 直做">」
Skills: <slug>@<path> loaded|skipped   # stage skill / Tier 1+ 必填
```

多 task 实现示例：`「Harness：orchestration:dispatcher-workflow」`

## 阶段门禁（Trae 强制）

**高于** AGENTS.md 自主性指令。完整表格、已批准判定与暂停回复格式见 **`harness-kit/core/routing.md` § 阶段门禁**。

**Trae 追加：** 仅 **WU 编排 + 委派子 Agent** 时：先 WORKTREE-INIT（§0），prompt 含 `worktree_path`。不派子 Agent 的简单任务在主 checkout 直接做，**不用** worktree。多 task 委派时主 Agent 不写业务代码（「小改动」除外）。

## 项目 Subagent 与 Task 补充

角色映射、readonly、Task 类型：

| agent_role | 机制 | 说明 |
| --- | --- | --- |
| coder | Trae Agent + `.agents/agents/coder.md` | 代码类 WU：实现+单测+自测+轻量审查 |
| implementer | Trae Agent + `.agents/agents/implementer.md` | 轻量 WU：docs/chore/config |
| reviewer | Trae Agent readonly + `.agents/agents/reviewer.md` | 独立审查（readonly） |
| explorer | Trae Agent readonly + `.agents/agents/explorer.md` | 只读探查 |
| debugger | Trae Agent + `.agents/agents/debugger.md` | 缺陷调查 |
| test-engineer | Trae Agent + `.agents/agents/test-engineer.md` | 测试/E2E 资产 |
| smoke-tester | Trae Agent + `.agents/agents/smoke-tester.md` | 提测前冒烟场景跑（不写测试代码） |
| web-investigator | Trae Agent + `.agents/agents/web-investigator.md` | 信息调研/网页搜索 |

委派示例：通过 Trae Agent 模式委派给对应的 subagent role。

详细 prompt 与返回格式：各 `.agents/agents/<role>.md`（Worker + 内嵌检查表）。

## Trae 硬约束（leader 行为总则见 `.trae/rules/leader.md`）

1. 路由判定 → 声明 `「Harness：…」`；遵守 **阶段门禁**
2. 需委派时：WORKTREE-INIT → 派发 WU；prompt 简练；`auto` 解析 SKILL 路径；无 `### Skills 使用` 不整合；并行 ≤3；维护 DISPATCH-TRACK
3. **GROUP 尾盘**：先集体测试（Write `*-collective-test.md`）→ 再集体审查（委派 `reviewer`，Leader Write `*-code-review.md`）；未过禁止声称批次完成
4. 整合子 Agent 结果后进入尾盘；`code_review: PASS` 不替代集体审查；可按 spec 合法 `SKIPPED`
5. 多 task 编排：激活 `orchestration` → Read `core/orchestration/dispatcher-workflow.md`
6. 文档审查：Load `document-review`；**代码**审查用 `requesting-code-review`（非 document-review）

## 何时委派 vs Leader 直做（Tier）

**Tier 2+ — 必须编排（`orchestration`）：** 见 `routing.md` § WU 编排硬触发。Leader **不得**主线程写业务代码。

**Tier 1 — Leader 直做：** 未命中硬触发；≥2 写文件或 fix/实现类。主 checkout；Write `verification-lite.md`；**不** WORKTREE / DISPATCH-TRACK。

**Tier 0 — 机械小改：** 单文件、无行为变更。无 FM；回复含验证即可。

**委派 subagent（Tier 2+ 或单点）：**

- 已批准 plan 中的 WU（代码 → `coder`；docs/chore/config → `implementer`；测试 / E2E → `test-engineer`；提测前冒烟 → `smoke-tester`）
- 实现后的审查（→ `reviewer`，不同实例）
- 跨 3+ 模块只读探索（→ `explorer`）
- 缺陷调查（→ `debugger`）
- 信息调研 / 网页搜索 / 截图取证（→ `web-investigator`）

**Leader 主线程（无 WU）：**

- Tier 0 / Tier 1（见上；Tier 1 须 verification-lite）
- 写 spec / plan / decision（写完后**暂停**）
- 范围不清晰（先 brainstorming）

**禁止用 Tier 0/1 规避：** plan 有 dispatch、≥2 WU、用户要求并行 → 必须 Tier 2+。

## Git（Leader）

见 **`harness-kit/core/routing.md` § Git 协作**。子 Agent 默认不 commit/push。

## 沟通语言

对用户回复、阶段门禁说明、子 Agent 派发 prompt 与整合反馈均使用**中文**（细则见 **`harness-kit/core/routing.md` § 沟通语言**）。代码标识符、路径、固定段键名（如 `### Skills 使用`）可保留英文。

## 禁止

- 未过阶段门禁修改业务代码
- 主 Agent 在实现阶段直接改代码（非小改动）
- 实现与审查同一 subagent 实例
- 无验证证据声称完成
- 跳过尾盘集体测试或集体审查（routing「小改动」除外）
- 未 Write `collective-test` / `code-review` 产物即写 execution-log「批次完成」
