# Skill 使用偏好说明

本文档是 Harness **所有角色在什么阶段用什么 skill** 的唯一维护入口。覆盖 Leader（Define / Plan / Ship）和 WU 子 Agent（Build / Verify / Review）。

---

## 生命周期总览

```
Define（Leader）→ Plan（Leader）→ Build+Verify+Review（WU）→ Ship（Leader）
```

- **Define / Plan / Ship**：Leader 本线程执行，不委派子 Agent。
- **Build / Verify / Review**：Leader 编排调度，委派 coder / debugger / reviewer 等 WU 执行。
- **Leader 直做（不分派子 Agent 时）**：所有 skill 都能用，没有角色/阶段限制。比如 Leader 直修 bug 可以加载 `systematic-debugging`、直写小功能可以加载 `incremental-implementation`。下文 § Leader 阶段列出的是该阶段的**最小集合**，Leader 可根据实际任务追加任意 skill。
- **verification-before-completion**：贯穿 Leader 和 WU 的全周期 skill，任何声称「完成」前必须加载。

---

## Leader 阶段

### Define：弄清要做什么

> 用户话术：「写方案」「出方案」「设计一下」

| 时机 | skill | 说明 |
|------|-------|------|
| 需求模糊，缺少 who/why/success/constraint | `interview-me` | 一问一答挖掘真实意图，产出 intent.md |
| 新项目 / 功能 / 重大变更 | `brainstorming` | 多方案对比，产出 spec.md |
| 方案涉及框架选型、API 用法 | `source-driven-development` | 读 package.json/go.mod，输出精确版本清单（STACK DETECTION） |
| 方案涉及多模块并行 | `api-and-interface-design` | 先定义 WU 间接口契约，再拆 WU |

**加载顺序：** `interview-me`（如需）→ `source-driven-development` → `brainstorming` → `api-and-interface-design`（如需）

**产物：** `.ai-runtime-artifacts/specs/`、`stack/`、`contracts/`

---

### Plan：拆解怎么实现

> 用户话术：「写计划」「制定实施计划」

| 时机 | skill | 说明 |
|------|-------|------|
| spec 已批准，需要拆成可执行步骤 | `writing-plans` | 拆 WU、标注依赖、产出 dispatch 图 |
| 过程中需要补充上下文 | `context-engineering` | 按阶段加载上下文，避免一次性塞满窗口 |

**产物：** `.ai-runtime-artifacts/plans/`、`*-dispatch.md`

---

### Ship：发布上线

> 用户话术：「发布」「上线」「提测」

| 时机 | skill | 说明 |
|------|-------|------|
| 尾盘通过，准备发布 | `shipping-and-launch` | Pre-launch Checklist：可逆、可观测、渐进式、有回滚 |
| 发布前埋点检查 | `observability-and-instrumentation` | 日志/指标/告警是否到位 |
| 代码提交、分支、MR | `git-xywh` | 三主干、五类临时分支、Angular 提交 |
| GitHub 操作（PR/CI/Actions） | `github` | `gh` CLI 交互，PR 创建与状态检查 |
| 文档审查（spec/plan/design） | `document-review` | 文档完整性审查，环境准备优先 |

**产物：** `.ai-runtime-artifacts/reviews/*-ship-check.md`

---

### Leader 跨阶段通用

| skill | 说明 |
|-------|------|
| `context-engineering` | 按阶段按需加载上下文，不一次性塞满 |
| `verification-before-completion` | 任何声称"完成"前必须有运行证据 |

---

## WU 阶段（子 Agent）

WU 由 Leader 通过 `orchestration` skill 派发。派发时 Leader 须将下方路由解析出的 skill 列表写入 prompt，禁止只写 `auto`。

> 下方路由仅决定 WU **被派发时**自动加载哪些 skill。Leader 直做时不受此限制，可使用任意 skill。

### Coder：写代码

Coder 按工作阶段加载 skill：

**动手前：**

| 阶段 | skill | 解决什么问题 |
|------|-------|-------------|
| 查文档 | `source-driven-development` | 涉及框架 API，先查官方文档，别凭记忆写 |
| 审决策 | `doubt-driven-development` | 重要设计决策时，拉新上下文做对抗审查 |

**写代码：**

| 阶段 | skill | 解决什么问题 |
|------|-------|-------------|
| 分步实现 | `incremental-implementation` | 多文件改动分步来，每步可运行可测试 |
| 边写边埋 | `observability-and-instrumentation` | 日志/指标/追踪跟代码一起写，不事后补 |

**收尾：**

| 阶段 | skill | 解决什么问题 |
|------|-------|-------------|
| 先写测试 | `test-driven-development` | 先写测试 → 看失败 → 写最小代码通过 |
| 运行证据 | `verification-before-completion` | 声称"做好了"之前，跑一遍验证命令 |
| 提交审查 | `requesting-code-review` | 完成后触发审查，通过才能收工 |

**特殊场景：**

| wu_type | 额外加载 | 说明 |
|---------|---------|------|
| `ui` | `ui-ux-pro-max`, `frontend-design`, `frontend-ui-engineering` | 设计库 → 视觉方向 → 工程化（a11y/性能） |
| `api` | `api-and-interface-design` | 先定契约，再写实现 |
| `review-fix` | `receiving-code-review` | 按审查意见改，先理解再动手 |

**完整加载顺序：**

```
source-driven-development → doubt-driven-development → incremental-implementation
→ observability-and-instrumentation → test-driven-development
→ verification-before-completion → requesting-code-review
```

UI 场景在前面加上：`ui-ux-pro-max → frontend-design → frontend-ui-engineering`

API 场景在前面加上：`api-and-interface-design`

review-fix 场景：`receiving-code-review → test-driven-development → verification-before-completion`

---

### 其他角色

| agent_role | wu_type | 加载 | 说明 |
|------------|---------|------|------|
| implementer | docs, config, chore | 无 | 纯体力活 |
| explorer | explore, * | 无 | 只读摸底 |
| explorer | investigate | `systematic-debugging` | 需要调查问题时 |
| debugger | bugfix, * | `systematic-debugging`, `source-driven-development`, `verification-before-completion` | 根因 → 文档 → 证据 |
| debugger | ui-bug | 同上 + `browser-testing-with-devtools` | UI bug 需要浏览器验证 |
| reviewer | review, * | `requesting-code-review`, `code-review-and-quality`, `verification-before-completion` | 五轴审查 + 验证 |
| security-auditor | review, * | `security-and-hardening`, `verification-before-completion` | OWASP + 验证 |
| perf-auditor | review, * | `performance-optimization`, `verification-before-completion` | 测量 → 优化 → 验证 |
| code-simplifier | simplify, * | `code-simplification`, `verification-before-completion` | 降复杂度 + 验证 |
| test-engineer | test | `test-driven-development`, `verification-before-completion` | 写测试 + 验证 |
| test-engineer | e2e | `browser-testing-with-devtools`, `verification-before-completion` | 浏览器验收 |
| smoke-tester | smoke | `agent-browser` 或 `browser-testing-with-devtools`（二选一，Leader 派发指定）+ `verification-before-completion` | 提测前冒烟场景跑 |
| web-investigator | research, * | `agent-browser` | 浏览器自动化 |

---

## Skill 清单

定义文件：`.agents/skills/<slug>/SKILL.md`

> 「谁用」列的 WU 指子 Agent 被派发时的默认分配。Leader 直做时不受此列限制，可按需加载任意 skill。

| 阶段 | slug | 用途 | 谁用 |
|------|------|------|------|
| Define | `interview-me` | 需求访谈，挖掘用户真实意图 | Leader |
| Define | `brainstorming` | 多方案对比设计 | Leader |
| Define | `source-driven-development` | 框架决策必须查官方文档 | Leader + WU |
| Define | `api-and-interface-design` | 契约优先，定义稳定接口 | Leader + WU(coder api) |
| Plan | `writing-plans` | 拆 WU、标注依赖、产出 dispatch | Leader |
| Plan | `context-engineering` | 按阶段加载上下文 | Leader + WU |
| Build | `doubt-driven-development` | 重要决策做新上下文对抗审查 | WU(coder) |
| Build | `incremental-implementation` | 薄垂直切片，每步可运行 | WU(coder) |
| Build | `observability-and-instrumentation` | 结构化日志 + 指标 + 追踪 | Leader + WU(coder) |
| Build | `frontend-design` | 高质量前端视觉设计 | WU(coder ui) |
| Build | `frontend-ui-engineering` | a11y + 状态管理 + 性能 | WU(coder ui) |
| Build | `ui-ux-pro-max` | UI/UX 设计系统检索 | WU(coder ui) |
| Verify | `test-driven-development` | 先写测试，再看失败，写最小代码 | WU |
| Verify | `verification-before-completion` | 完成前必须有运行证据 | Leader + WU |
| Verify | `systematic-debugging` | 先定位根因再修复，禁止猜测试错 | WU(debugger/explorer) |
| Verify | `browser-testing-with-devtools` | Chrome DevTools 实时测试 | WU(test-engineer/debugger/smoke-tester) |
| Verify | `receiving-code-review` | 按审查意见改代码 | WU(coder review-fix) |
| Review | `requesting-code-review` | WU 轻量审查 + GROUP 集体审查 | WU(coder/reviewer) |
| Review | `code-review-and-quality` | 五轴审查：正确性/可读性/架构/安全/性能 | WU(reviewer) |
| Review | `security-and-hardening` | OWASP Top 10 安全审查 | WU(security-auditor) |
| Review | `performance-optimization` | 先测量再优化，CWV/N+1/Bundle | WU(perf-auditor) |
| Review | `code-simplification` | 降低复杂度，保持行为不变 | WU(code-simplifier) |
| Review | `document-review` | 文档完整性审查 | Leader |
| Ship | `shipping-and-launch` | Pre-launch Checklist + 回滚方案 | Leader |
| Ship | `git-xywh` | 三主干、五类分支、Angular 提交 | Leader |
| Ship | `github` | GitHub CLI（gh）交互 | Leader |
| — | `agent-browser` | 浏览器自动化（Playwright） | WU(web-investigator/smoke-tester) |
| — | `orchestration` | 多任务并行编排调度 | Leader |

---

## 按任务快速查表

| 用户要做什么 | 谁做 | 用哪些 skill |
|-------------|------|-------------|
| 写方案 / 设计 | Leader | `interview-me`(如需) → `source-driven-development` → `brainstorming` |
| 写实施计划 | Leader | `writing-plans` |
| 写业务代码 | WU(coder) | 见上文 § Coder |
| 写 UI | WU(coder ui) | § Coder + ui-ux-pro-max / frontend-design / frontend-ui-engineering |
| 写 API | WU(coder api) | § Coder + api-and-interface-design |
| 审查被打回后改 | WU(coder review-fix) | § Coder review-fix |
| 文档 / 配置 / 杂项 | WU(implementer) | 无 |
| 只读摸底 | WU(explorer) | 无 |
| 调查 bug | WU(debugger) | systematic-debugging → source-driven-development → verification-before-completion |
| 实现后审查 | WU(reviewer) | requesting-code-review → code-review-and-quality |
| 安全审查 | WU(security-auditor) | security-and-hardening → verification-before-completion |
| 性能审查 | WU(perf-auditor) | performance-optimization → verification-before-completion |
| 代码简化 | WU(code-simplifier) | code-simplification → verification-before-completion |
| 补测试 | WU(test-engineer) | test-driven-development → verification-before-completion |
| E2E 验收 | WU(test-engineer e2e) | browser-testing-with-devtools → verification-before-completion |
| 提测前冒烟 | WU(smoke-tester smoke) | agent-browser 或 browser-testing-with-devtools（Leader 指定）→ verification-before-completion |
| 网页搜索/调研 | WU(web-investigator) | agent-browser |
| 提交 / MR | Leader | git-xywh |
| 发布 / 上线 | Leader | shipping-and-launch → observability-and-instrumentation |
| GitHub 操作 | Leader | github |
| 文档审查 | Leader | document-review |
| 跑一条命令 | shell Task | 无 |

---

## 派发字段

| 字段 | 含义 |
|------|------|
| wu_type | feature \| bugfix \| ui \| chore \| refactor \| review-fix | smoke \| api \| docs \| config \| test \| e2e \| explore \| review \| simplify \| investigate \| ui-bug \| research |
| wu_skills | 逗号分隔 slug，或 `auto`（查本文档） |
| agent_role | coder \| implementer \| explorer \| debugger \| reviewer \| security-auditor \| perf-auditor \| code-simplifier \| test-engineer \| smoke-tester \| web-investigator |

Leader 派发 WU 时：必须将解析出的 slug 写入 prompt，禁止只写 `auto`。子 Agent 返回时须包含 `### Skills 使用`。

---

## 加载路径

平台差异见适配器 `bindings.md`。通用查找顺序：

1. `.agents/skills/<slug>/SKILL.md`（项目共享层，优先）
2. 平台层：`.cursor/skills/`、`.claude/skills/`、`.trae/skills/`
3. `~/.agents/skills/<slug>/SKILL.md`（用户全局）

---

## References 纪律

Leader 派发 WU 时，必须将关联 references 的 checklist 条目注入 Context Block。WU 返回时：

- 产物中包含 `### References 检查`
- 逐条标注 `pass / fail / n/a`
- 任一 `fail` → `wu_status: blocked`，Leader 不得整合

Leader 尾盘 / Ship Gate：全量 references 自检，写入 collective-test.md 或 ship-check.md。

---

## 维护

- 改 Leader 阶段路由：改本文档 § Leader 阶段
- 改 WU 路由：改本文档 § Coder 或 § 其他角色
- 增删 skill：改本文档 § Skill 清单 + 对应路由节
- 项目专有 skill：放适配器 skill 目录，通过 `wu_skills` 手写或 `overrides` 追加
