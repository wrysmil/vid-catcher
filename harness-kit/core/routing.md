# Harness Routing

路由判定与阶段门禁的**单一真相源**。入口文件（`AGENTS.md`、适配器入口）只保留指针，细则以本文件为准。

## 总原则

- 默认 route 是强制基线。用户指定 skills 或工具时，默认理解为追加要求，不替代本文件的默认 route。
- 只有当用户明确说“不要使用默认 skills / 只使用某个 skill / 禁用某个 route”时，才允许跳过默认 route，并必须在回复或产物 front matter 中说明原因。
- 方案设计优先使用 `superpowers:brainstorming`；该阶段向用户提问时**优先**使用环境内 ask 类结构化工具（无则对话提问）。
  - **需求不明确时**：在 brainstorming 之前先走 `interview-me`（agent-skills）。触发条件：缺少 who/why/success/constraint 中任一项，或需求使用惯例化表述（"做个仪表盘"而非具体描述）。详见 `core/orchestration/dispatcher-workflow.md` § Superpowers 衔接。
  - **方案设计前必执行 STACK DETECTION**：Load `source-driven-development`，读取 `package.json` / `go.mod` 等依赖文件，输出精确版本清单。产物写入 `.ai-runtime-artifacts/stack/YYYY-MM-DD-stack.md`。
  - **多 WU 并行前必定义接口契约**：Load `api-and-interface-design`，在 writing-plans 拆分 WU 之前识别 WU 间接口边界，定义端点签名/错误格式/分页约定。产物写入 `.ai-runtime-artifacts/contracts/YYYY-MM-DD-contract-<name>.md`。
- 已批准设计后的实施计划使用 `superpowers:writing-plans`。
- 多 task 编码、并行执行、复杂审查和验证修复：
  - **全平台**：`orchestration` → `core/orchestration/dispatcher-workflow.md`
- **Tier 0** 单文件机械修改：Leader 直做，无 FM（见 § 任务 Tier）。
- **Tier 1+** 简单实现：Leader 直做或编排（见 § WU 编排硬触发）。
- **文档优先（强制）：** 任何实现任务（Tier 1+）必须先扫描 `.ai-runtime-artifacts/` 中与当前任务相关的 specs/plans/decisions/contracts/research，再读 `project.profile.md` + `context-map.md`。**跳过此步骤直接写代码 = 未按 harness 执行**。跨会话的文档是桥 — 读它们就不需要「每次重新调教」。细则见 `source-driven-development` skill Step 0 及 § 按判定加载「Leader 直做 / Tier 1」。
- 项目级 skill 优先于通用 skill。
- **Git 协作**：组织级分支、提交、MR、热修、合流默认 invoke **`git-xywh`** skill；本项目差异与 AI 约束见 `harness-kit/project.git.md`（不将 skill 全文复制进仓库）。

## 平台原生 plan 工具（禁止使用）

**Claude Code 的 `EnterPlanMode` / `ExitPlanMode`、Cursor 的 Plan 模式** 等**平台原生 plan 工具**会把 plan 写到平台私有目录（`~/.claude/plans/`、Cursor 内部），**完全绕过** Harness 的 stage skill 流程、`plan.harness-overlay.md` 契约与 `.ai-runtime-artifacts/plans/` 落盘规则。一旦走原生工具，本会话**无法**做 plan 门禁拦截、executor 不会把 plan 当 Harness 产物、用户也看不到完整 plan body。

**规则：**

| 任务 | 走 Harness | 禁止 |
| --- | --- | --- |
| 写实施计划 | Load `writing-plans` skill → `artifact-templates/plan.harness-overlay.md` → Write `.ai-runtime-artifacts/plans/YYYY-MM-DD-<topic>-plan.md` | Claude Code `EnterPlanMode` / `ExitPlanMode`、Cursor Plan 模式 |
| 写方案 | Load `brainstorming` skill → `artifact-templates/spec.harness-overlay.md` → Write `.ai-runtime-artifacts/specs/...` | 平台原生 plan/spec 工具 |

**为什么用平台原生工具是 bug：**

1. 产物落到 `~/.claude/plans/` 或 Cursor 内部，**不进 git**、不进 `.ai-runtime-artifacts/` FM 元数据、不被 `harness-check.sh` 扫描、不进 review/verification 链
2. 用户批准时只看到 plan body，**看不到 FM/evidence 段**；与「计划门禁」语义脱节
3. 同名 `plans/` 在两套目录分裂，后续 `harness-kit check` / `git log` / `requesting-code-review` 全部漏抓

**根因与修复（用户在会话中触发时）：**

- 若 agent 已走原生工具 → 立刻 `cat ~/.claude/plans/<name>.md >> .ai-runtime-artifacts/plans/YYYY-MM-DD-<topic>-plan.md`、补 Harness FM（`route: superpowers:writing-plans`、`skills_evidence`、`## Next`），然后从原 native 路径继续；不要把 plan 留在 `~/.claude/plans/`
- 项目级 opt-in 强阻断：在 `CLAUDE.md` 或 `AGENTS.md` 中添加禁止规则说明，或在用户触发时进行干预。



## 用户指定 Skills 的合并规则

用户在任务中指定 skills 时，按下面规则合并：

| 用户表达 | 执行方式 |
| --- | --- |
| “用 X skill 做这件事” | 先执行默认 route，再叠加 X skill |
| “参考 X 风格 / 用 X 发布” | 先执行默认 route，再在对应阶段使用 X |
| “只用 X / 不要用默认 skill / 禁用 Y” | 按用户排除项执行，并记录跳过默认 route 的原因 |
| 用户指定 skill 与默认 route 冲突 | 先说明冲突，再选择满足用户强约束的最小 route |

示例：用户要求“按 writing-style 写文章并发飞书”，默认 route 仍应是 `superpowers:brainstorming -> writing-style -> lark-doc`，而不是只执行 `writing-style -> lark-doc`。

## 用户话术 → Route

| 用户说 | Route | 本阶段禁止 |
| --- | --- | --- |
| 写方案 / 出方案 / 设计一下 | `brainstorming` | 改业务代码、写 plan、实现、派子 Agent |
| 写计划 / 实施计划 | `writing-plans` | 改业务代码、实现、派子 Agent |
| 开始实现 / 直接做 / 并行执行 | 实现（见路由表） | —（须已过 spec/plan 门禁或属小改动） |
| 发布 / 上线 / 提测 / 预发 / 灰度 | Ship Gate（见路由表） | 改业务代码、新 feature |

仅说「写方案」→ **只** Write `specs/` 并暂停；不得同轮进入 plan 或实现。细则见适配器 `bindings.md` 文件写入门禁绑定。

### 组合指令（同句多阶段）

用户**一句**里同时出现设计/计划 **与** 实现/执行（如「写计划然后执行」「出方案并直接做」）：

| 规则 | 说明 |
| --- | --- |
| **只执行前一阶段** | 本轮回合仅完成 spec 或 plan，**暂停** |
| **不得** | 因句末「然后执行/直接做」在本轮改业务代码、激活编排 skill、Write Tier 1+ 实现产物 |
| **回复须说明** | 「plan 已写入；请在本会话说 **开始实现** 后继续」 |
| **例外** | 用户**同时**明确「spec/plan 也不用等我确认」→ 可写 FM `approved: true` 并注明原话 |

「之后都默认你推荐的就好」**不**构成上述例外（见 § 阶段门禁）。

## 任务 Tier（产物分级）

| Tier | 名称 | 典型场景 | 产物 |
| --- | --- | --- | --- |
| **0** | 机械小改 | 单文件 typo、改常量、纯格式化 | **无** FM；回复含验证摘要即可 |
| **1** | Leader 直做 | ≥2 写文件、bugfix、小 feature、配置变更、用户说 fix/实现但未走 WU | **`verifications/*-verification-lite.md`**（模板 `verification-lite.md`） |
| **2+** | 编排交付 | 多 task、有 `*-dispatch.md`、并行 WU、批次尾盘 | spec/plan/dispatch、execution-log、collective-test、code-review 等 |

**升级规则：** 执行中发现 Tier 估低 → 立即补 Tier 1 产物或暂停升级 spec/plan。

**Tier 0 硬条件（须同时）：** 仅 **1** 个写文件；无新增测试；无行为变更；用户未说「实现/fix/审查」。

**Tier 1 触发（任一即须）：** ≥2 写文件；跑过测试/lint；用户说 fix/实现/改 bug；Leader 直做已批准 plan 且不委派 WU。

**Tier 1 自上下文打包（必执行）：** Leader 在开始写代码前必须执行 Self-Context Pack（见 `core/orchestration/dispatcher-workflow.md` §步骤 0.5 Tier 1 自打包）。**首步必须扫描 `.ai-runtime-artifacts/` 中与任务相关的产物**（`specs/`、`plans/`、`decisions/`、`contracts/`、`research/`），然后读取 project.profile.md（L1）、相关 spec 章节（L2）、目标源文件 ≤5 个（L3）、参考范例、明确约束。必须先 Load `source-driven-development` skill → 执行 Step 0（项目文档检查）→ 再进入编码。不执行上下文准备的 Tier 1 实现视为不规范。

**禁止：** 用 Tier 0 规避 Tier 1；用 Tier 1 Leader 直做规避 Tier 2 编排（见下节硬触发）。

### WU 编排硬触发（Tier 2+，不得 Leader 直做）

满足 **任一** 须编排调度（见适配器 `bindings.md`；不得仅 Tier 1）：

- plan FM 的 `dispatch:` **非** `n/a`，或存在 `*-dispatch.md`
- plan 内 **≥2** 个可并行 WU / GROUP
- 用户说「并行」「多 task」「开始实现」且已有 **已批准** plan
- 预计 **≥3** 个写文件且非纯 docs/chore

不满足上表且 scope 有界 → 允许 Tier 1 Leader 直做。

## 路由表

| 任务类型 | Capability | Cursor | Claude | 产物 |
| --- | --- | --- | --- | --- |
| 需求澄清（按需前置） | `skills.stage-load` | Load `interview-me` → Write intent | 同左 | `.ai-runtime-artifacts/specs/YYYY-MM-DD-<topic>-intent.md` |
| 需求澄清 / 方案设计 / 行为变更 | `skills.stage-load` + design | `source-driven-development`（STACK）+ `superpowers:brainstorming` → `api-and-interface-design`（多 WU 时） | 同左 | `.ai-runtime-artifacts/specs/` + `stack/` + `contracts/` |
| 实施计划 | `skills.stage-load` + plan | `superpowers:writing-plans` | 同左 | `.ai-runtime-artifacts/plans/` |
| 多 task 编码 / 并行实现 | `orchestration.dispatch` | `orchestration` | `orchestration` | `.ai-runtime-artifacts/execution-logs/` + 代码变更 |

> 上表 Cursor/Claude 列为平台特定绑定摘要；完整绑定见各适配器 `bindings.md`。
| 验证 / 跑命令证据 | `skills.stage-load` | `superpowers:verification-before-completion` | 同左 | `.ai-runtime-artifacts/verifications/` |
| 代码审查（尾盘/批次） | `orchestration.collective-closeout` | `requesting-code-review` + `code-review-and-quality` | 同左 | `.ai-runtime-artifacts/reviews/` |
| **批次收尾（尾盘）** | `orchestration.collective-closeout` | `verification-before-completion` → 并行扇出 `requesting-code-review` + `security-and-hardening`（+ `performance-optimization` 按需） | 同左 | `verifications/*-collective-test.md` + `reviews/*-code-review.md` + `reviews/*-security-review.md` + execution-log |
| 缺陷调查 | `roles.debugger` | `superpowers:systematic-debugging` | 同左 | `.ai-runtime-artifacts/specs/` 或 `verifications/` |
| 验证 / 修复循环 | — | `verification-before-completion` | 同左 + reviewer | `verifications/` + `reviews/` |
| 架构决策 | — | Task 只读 × 多轮 | 同左 | `.ai-runtime-artifacts/decisions/` |
| 信息调研 / 网页搜索 | `roles.web-investigator` | web-investigator | Task + web-investigator.md | `.ai-runtime-artifacts/research/` |
| 文章 / 知识沉淀 / 对外文档 | — | brainstorming + 写作 skill | 同左 | `retros/` 或用户指定 |
| 小改动 / Tier 0 机械修改 | — | 直接处理 | 同左 | 无 FM（回复含验证） |
| Leader 直做 / Tier 1 简单实现 | `skills.stage-load` | 直做 + verification | 同左 | `verifications/*-verification-lite.md` |
| 建分支 / 提交 / rebase / MR·PR | `git.worktree-script` + git-xywh | `git-xywh` + `project.git.md` | 同左 | 无（或 MR 链接） |
| 热修 / 提测线 / 合流 / 标签 | — | `git-xywh` + `project.git.md` | 同左 | 无 |
| Harness 脚手架变更 | — | `git-xywh` chore | 同左 | 与业务 commit 分离 |
| **发布上线 / Ship Gate（尾盘后）** | `orchestration.ship` | `shipping-and-launch` + `observability-and-instrumentation` | 同左 | `.ai-runtime-artifacts/reviews/*-ship-check.md` + `retros/` |
| 文档审查 | — | `superpowers:document-review` | 同左 | `.ai-runtime-artifacts/reviews/` |

## 按判定加载

完成路由判定后，**仅**加载下表对应文件（小改动：声明后直接处理，无需读本表；叠加 skill 时次行 `Skills:` 声明，用时再 Load）。

| 判定（路由表 / 用户任务） | 再读（按序） |
| --- | --- |
| 小改动 / Tier 0 | 无 stage skill；回复须含改动摘要 + 验证命令输出 |
| 需求澄清（按需前置） | **①** Load `interview-me` → **②** Write `.ai-runtime-artifacts/specs/YYYY-MM-DD-<topic>-intent.md`（FM: route=interview-me, confidence, confirmed）。用户显式确认后才进入方案设计。 |
| Leader 直做 / Tier 1 | **①** Load `source-driven-development` → 执行 **Step 0**：扫描 `.ai-runtime-artifacts/`（`find .ai-runtime-artifacts/ -name "*<topic>*.md"`）→ Read 1-3 个最相关产物 → **②** Self-Context Pack（读 `project.profile.md`、相关 spec 章节、目标源文件 ≤5 个、参考范例）→ **③** Load `verification-before-completion` → **④** `project.verification.md` → **⑤** Write `verification-lite.md` |
| 需求澄清 / 方案设计 | **①** 先扫描 `.ai-runtime-artifacts/` 中已有相关产物（避免重复设计）→ **②** Load `source-driven-development`（STACK DETECTION：读 `package.json` 等 → Write `.ai-runtime-artifacts/stack/`）→ **③** Load `brainstorming` → **④** `artifacts.md` → **⑤** 澄清起步后，涉及模块时再读 `project.profile.md`、`context-map.md`。多 WU 并行时 **⑥** Load `api-and-interface-design` → Write `.ai-runtime-artifacts/contracts/`。**禁止**未 Load skill 前用 profile/扫代码代替 brainstorming。 |
| 实施计划 | **①** 先扫描 `.ai-runtime-artifacts/specs/` 中相关方案 + `.ai-runtime-artifacts/plans/` 中已有计划 → **②** Load `writing-plans` → **③** `artifacts.md` → **④** `plan.harness-overlay.md`（FM + Next）；并行时 **⑤** 另写同 stem `*-dispatch.md`（`dispatch.harness-overlay.md`）。 |
| 多 task 编码 / 并行实现 | **文档优先扫描** `.ai-runtime-artifacts/`（specs/plans/decisions/contracts/research）→ 编排调度 skill → `core/orchestration/dispatcher-workflow.md`；§0 WORKTREE-INIT → §0.5 ContextPack（上下文打包，含相关 artifacts）→ §1 执行图 → §2 SpawnWorker；`core/orchestration/skill-preferences.md`；具体绑定见适配器 `bindings.md` |
| 验证 / 跑命令 | **①** Load `verification-before-completion` → **②** `project.verification.md` |
| 代码审查（尾盘/批次） | **①** Load `requesting-code-review` + `code-review-and-quality` → **②** 委派 reviewer；并行 **③** Load `security-and-hardening` → 委派 security-auditor；按需 **④** Load `performance-optimization` → 委派 perf-auditor |
| **GROUP 收尾 / 批次交付 / 「收尾」「提测前检查」** | **①** `verification-before-completion` → `project.verification.md` → `artifact-templates/collective-test.md` **②** 并行扇出 `requesting-code-review` + `security-and-hardening`（+ `performance-optimization` 按需）**③** `core/orchestration/dispatcher-workflow.md` § 步骤 3 **④** batch-closeout spec |
| 缺陷调查 | **①** Load `systematic-debugging` → **②** `source-driven-development`（STACK DETECTION）→ **③** `project.profile.md`；委派见适配器 `bindings.md` |
| 信息调研 / 网页搜索 | 委派 web-investigator → `.agents/agents/web-investigator.md`（见适配器 bindings） |
| Git（提交 / 分支 / MR 等） | **`git-xywh` skill** + `project.git.md` |
| 架构决策 | `artifacts.md` + `artifact-templates/decision.md` |
| runbook 明示任务 | 按 routing.md 对应判定处理 |
| **发布上线 / Ship Gate（尾盘后）** | **①** Load `shipping-and-launch` → Pre-Launch Checklist → **②** Load `observability-and-instrumentation` → 埋点/告警/日志检查 → **③** Write `.ai-runtime-artifacts/reviews/YYYY-MM-DD-ship-check.md`（FM: route=orchestration.ship, artifact=ship-check） |
| 文档审查 | **①** Load `document-review` → **②** 根据文档类型加载 `review-rules/*.md` |

**禁止：** 在未判定 route 前预读 `core/orchestration/dispatcher-workflow.md`、`skill-preferences.md` 或全套 `project.*`。

**Skill 产物：** 上表中带 stage skill 的阶段，正文以已 Load 的 `SKILL.md` 为准；`artifact-templates/spec.md` / `plan.md` 仅为 redirect stub。契约与门禁见 `spec.harness-overlay.md`、`plan.harness-overlay.md`；执行图见 `dispatch.harness-overlay.md`。无 stage skill 的编排产物仍用 `artifact-templates/`（execution-log、track、handoff 等）。

### Git worktree

| 场景 | worktree | 代码目录 |
| --- | --- | --- |
| 小改动 / Leader 主线程直接实现（**不拆 WU、不委派** worker） | **跳过** | 主 checkout |
| 编排调度且将委派写代码类 worker | **必须** WORKTREE-INIT | `worktree_path` |

用户说「开始实现」但任务仍属 Leader 直接处理时，**不得**仅为该句创建 worktree。  
具体 worktree 机制见适配器 `bindings.md`。

### Tier 与小改动判定

**Tier 0（见 § 任务 Tier）：** 仅聊天 + 验证摘要，无 FM。

**以下不属于 Tier 0**（至少 Tier 1；满足 WU 硬触发则 Tier 2+）：

- ≥2 个写文件
- 用户要求 fix / 实现 / 改 bug / 审查
- 涉及 3 个以上文件的 diff 分析
- 作为实施流程末尾的验证步骤
- 需要跨模块理解才能给出结论
- plan 已存在且 `dispatch:` 非 `n/a`

## 阶段门禁

写入下列产物后**须暂停**，等用户在本会话明确继续，再进入下一阶段。此规则优先于 AGENTS.md 自主性指令。

| 阶段 | 产物 | 暂停后用户可说 |
| --- | --- | --- |
| 设计完成 | `.ai-runtime-artifacts/specs/` | 「写计划」「制定实施计划」「直接实现」「直接做」或给修改意见 |
| 计划完成 | `.ai-runtime-artifacts/plans/` | 「开始实现」「并行执行」或给修改意见 |
| 决策完成 | `.ai-runtime-artifacts/decisions/` | 「执行」 |

**已批准** = 用户在本会话**单独说过**上表继续指令（如「开始实现」），或任务开头一次性授权且 FM 写 `approved: true` + 引用原话。

**不算已批准：** 同句组合指令中的「然后执行/直接做」（见 § 组合指令）；仅写 plan 的同轮 continuation。

**用户说「之后都默认你推荐的就好」** = 仅跳过方案**选择**讨论；**不跳过** spec/plan 写入后的审查暂停，除非用户同时说「spec/plan 也不用等我确认」。

**同轮禁止：** Write `specs/` / `plans/` / `decisions/` 后，**同一轮**不得改业务代码、委派子 Agent、WORKTREE-INIT、Read 并执行 `dispatcher-workflow.md`。

**暂停时回复须包含：** 产物路径、摘要、以及 artifact 模板 `## Next` 中的选项。

**实现阶段：** 仅当走 WU 编排且**委派** worker 时：先 **WORKTREE-INIT**，worker cwd = `worktree_path`，主 checkout 不写业务代码。不拆 WU、不派 worker 的简单任务在主 checkout 直接做，**不用** worktree。详见 `dispatcher-workflow.md` §0。

**交付完成：** 本 GROUP / 批次全部 WU 返回后，**默认进入尾盘**（集体测试 → 集体审查 → Leader 落盘两产物 → 更新 execution-log）。**完成** ≠ 末个 WU 返回；须满足 `docs/superpowers/specs/2026-05-28-batch-closeout-review-and-collective-test.md` §4（小改动除外）。

## Git 协作

| 规则 | 说明 |
| --- | --- |
| 组织规范来源 | **`git-xywh` skill**（三主干、五类临时分支、Angular 提交、MR 流程） |
| 项目差异来源 | **`harness-kit/project.git.md`**（MR 平台、commitlint、是否允许 AI push、Harness 独立 commit 等） |
| 谁执行 Git | **Leader / 主 Agent**；`coder` / `implementer` 等子 Agent 默认不 commit/push |
| 与默认 route 关系 | Git 任务在对应阶段**叠加** `git-xywh`（例如实现完成后的提交不替代 `verification-before-completion`） |
| skill 未安装 | 说明缺失，按 `project.git.md` 与仓库已有配置（`.husky`、`commitlint`、CI）执行；运行 `bash harness-kit/scripts/install-ai-skills.sh` 检查路径 |
| **如何 invoke** | 有 Skill 工具 → 加载 **`git-xywh`**；否则 Read 本机 skill 文件（见 `project.git.md` § 如何调用）。 |

**Harness 声明示例：** `「Harness：git-xywh + project.git.md」`（用户仅说「提交代码」时）

**注意：** 路由表中的 `git-xywh` 指**必须先加载该 skill 正文**再执行 git，不是仅阅读 `project.git.md` 或 `routing.md` 即够。

## 阶段指定 skill 必用

- 路由表 **Route 列**写明的 skill：本阶段**必须** Load（Read `SKILL.md` 或 Skill 工具）并按流程执行；未写明的**不**强制。
- Load 后**不得**用 `artifact-templates` 同名 stub/旧提纲的正文替代 skill；Harness 仅提供 overlay（FM、`## Next`、dispatch 指针，见 `artifacts.md`）。
- 有阶段 skill：先 Load → 再交付该阶段产物；`skills` 非空且与 route 一致（见 `artifacts.md`）。
- 子 Agent：prompt「本 WU Skills」所列**必须** Load；返回须 `### Skills 使用`，否则 Leader 不整合。
- 小改动 Tier 0：无 stage skill；次行 `Skills:` 仅在有叠加 skill 时
- 会话声明（**统一格式，全平台**）：
  - 首行：`「Harness：<route 或 "Tier 0 小改动" | "Tier 1 Leader 直做">」`
  - 次行（有 stage/route skill 或 Tier 1+）：`Skills: <slug>@<path> loaded|skipped`
- Tier 1+ 完成前须 Load `verification-before-completion` 并落盘或回复附命令输出

## 沟通语言

- **对用户：** 会话回复、阶段门禁暂停说明、方案/计划摘要与验收口径均使用**中文**。
- **子 Agent 协调：** 派发 prompt、整合反馈、`DISPATCH-TRACK` 与要求子 Agent 返回的正文使用**中文**。
- **例外：** 代码标识符、文件路径、命令、API 名、固定段键名（如 `### Skills 使用`、`wu_status`）可保留英文；用户明确要求其他语言时从其要求。

## 文件写入（强制）

- 改仓库内文本（源码、配置、`.ai-runtime-artifacts/`）**只用** `Write` / `Edit`；改前先 `Read`
- **Shell 仅用于** 测试、lint、构建、git、只读查询
- **禁止** Shell 写文本（`Set-Content`、`Out-File`、`echo … >`、`type … >`、无 `encoding='utf-8'` 的 Python/Node 一行写文件）
- 默认 **UTF-8 无 BOM**（含中文）

## 运行约束

- **强制声明：** 首行 `「Harness：…」`；次行 `Skills:` 格式见 § 阶段指定 skill 必用（Tier 1+ 或 stage skill 时必填）
- **未声明时的用户干预：** 首句无 `「Harness：…」` → 发送：`请先读取 CLAUDE.md 和 harness-kit/core/routing.md，按 harness 规范重新处理我的上一个请求。`
- **跳过门禁时的干预：** `你跳过了阶段门禁。我只要求写方案/计划，不要改代码。写入 .ai-runtime-artifacts/ 后暂停等我确认。`
- **跳过文档扫描时的干预：** `你没有先扫描 .ai-runtime-artifacts/ 中的相关产物就开始写代码。请先 Load source-driven-development skill → 执行 Step 0（扫描项目文档）→ 找到并阅读相关 specs/plans/decisions，然后再开始实现。`
- **走平台原生 plan 工具时的干预：** `你用了 Claude Code EnterPlanMode / Cursor Plan 模式，绕过了 Harness。撤回该 plan，Load writing-plans skill 重新写 .ai-runtime-artifacts/plans/YYYY-MM-DD-<topic>-plan.md（FM + Next + dispatch）。`
- 执行非小型任务前，先在过程产物或回复中声明本次 route、skills 和 source。
- route 必须同时体现默认 skills 和用户指定 skills；如果跳过默认 skills，必须记录用户的明确排除指令。
- **Cursor / Claude / Trae**：委派 worker 前写清 WU 目标、文件列表、禁止事项与 done criteria；worker 输出须由主 Agent 整合并验证后再落地。具体委派方式见适配器 `bindings.md`。
- 任何完成声明前必须有验证证据。
