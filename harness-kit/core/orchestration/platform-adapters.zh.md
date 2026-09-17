# 平台适配（harness-kit）

本文档是 harness-engineer `platform-adapters.md` 的 harness-kit 中文版改编，**多平台并列**。  
上游版本见 `VENDOR.md`。

---

## 沟通语言（所有平台）

Leader 与子 Agent 之间：派发、返回摘要、整合与追踪日志的正文使用**中文**。细则见 `harness-kit/core/routing.md` § 沟通语言。**Cursor / Claude / Trae 一律遵循**。

## 平台检测

| 信号 | 平台 |
| --- | --- |
| Cursor 工作区 + `.cursor/rules/` | cursor |
| CLAUDE.md 会话 + Skill 工具 + 无 Cursor | claude |
| Trae 工作区 + `.trae/rules/` | trae |
| 否则 | generic |

在 execution-log 的 front matter 中记录 `platform: cursor | claude | trae | generic`。

---

## Cursor 角色映射

| Harness 角色 | Cursor 机制 |
| --- | --- |
| 编排者（Leader） | 主 Agent（Composer / Agent 模式） |
| 实现 / 审查 / 探查 / 调试 | **`.agents/agents/<role>.md`** 共享 subagent |
| Shell / 测试 / 构建 | Task `shell`（补充） |
| CI 失败 | Task `ci-investigator`（补充） |
| 项目规则 | `.cursor/rules/`、`AGENTS.md`、`harness-kit/core/` |
| 生命周期钩子（可选） | 用户自行配置 `.cursor/hooks.json` |

### 共享 Subagent（`.agents/agents/`）

| 文件 | 用途 |
| --- | --- |
| `coder.md` | 代码类 WU：实现、单测、自测、开发者自检 |
| `implementer.md` | 轻量 WU（docs/chore/config） |
| `reviewer.md` | 独立审查（readonly） |
| `explorer.md` | 只读探查 |
| `debugger.md` | 缺陷调查 |
| `test-engineer.md` | 测试 / E2E 资产 |
| `web-investigator.md` | 网探：信息搜索、网页浏览、截图取证 |

共享 skill（`.agents/skills/`）与平台 skill（`.cursor/skills/`）：见 `core/orchestration/skill-preferences.md`。

源模板：`harness-kit/.agents/`（bootstrap 投影到项目根 `.agents/`）。

详细 prompt 与返回格式见各 `.agents/agents/<role>.md` 文件。

### Task 内置类型（补充）

| 类型 | 用途 |
| --- | --- |
| `explore` | 无 explorer 时的只读搜索 |
| `shell` | 测试、构建、脚本 |
| `ci-investigator` | CI 失败根因 |

---

## 平台默认参数

阶段门禁见 `harness-kit/core/routing.md` § 阶段门禁。

### Cursor

```yaml
max_parallel_agents: 3      # 上限 5；遇限流则降低
loop_mode: single-pass      # 默认；continuous 需显式 opt-in
subagent_spawn: .agents/agents/<role>.md  # 共享层
monitoring: 轮询后台 Task 与终端输出
```

配置模板：`harness-kit/platform/cursor/.cursor/config.defaults.yaml`

### Claude Code

```yaml
max_parallel_agents: 3      # 同 Cursor；硬顶 5
loop_mode: single-pass      # 默认；continuous 需显式 opt-in + HANDOFF（见 claude-continuous-loop.md）
subagent_spawn: Task(subagent_type=generalPurpose) + .agents/agents/<role>.md  # 共享层
monitoring: 全部状态落盘到 .ai-runtime-artifacts/，跨会话由 HANDOFF 接力
hooks: 用户自行配置（可选）
```

### Trae

```yaml
max_parallel_agents: 3      # 同上
loop_mode: single-pass
subagent_spawn: Trae Agent + .agents/agents/<role>.md
monitoring: Trae 终端输出
```

---

## Claude 角色映射

| Harness 角色 | Claude 机制 |
| --- | --- |
| 编排者（Leader） | 主会话（CLAUDE.md + AGENTS.md） |
| 实现 / 审查 / 探查 / 调试 | **Task(subagent_type=generalPurpose)** + `.agents/agents/<role>.md` 作 prompt |
| Shell / 测试 / 构建 | Task |
| 项目规则 | `CLAUDE.md`、`AGENTS.md`、`harness-kit/core/` |
| 生命周期钩子 | `.claude/settings.json`（PreToolUse / PostToolUse / Stop） |

共享 skill（`.agents/skills/`）与平台 skill（`.claude/skills/`）：见 `core/orchestration/skill-preferences.md`。

---

## Trae 角色映射

| Harness 角色 | Trae 机制 |
| --- | --- |
| 编排者（Leader） | Trae Agent 模式（自主规划+执行） |
| 实现 / 审查 / 探查 / 调试 | **Trae Agent** + `.agents/agents/<role>.md` |
| Shell / 测试 / 构建 | Trae Agent Task |
| 项目规则 | `.trae/rules/`、`AGENTS.md`、`harness-kit/core/` |
| 生命周期钩子 | 用户自行配置 |

共享 skill（`.agents/skills/`）与平台 skill（`.trae/skills/`）：见 `core/orchestration/skill-preferences.md`。

---

## 平台限制与缓解

### Cursor

| Cursor 限制 | 缓解 |
| --- | --- |
| 无内置 cron | 后台 Task 每 2–3 分钟轮询；可用 `/loop` skill |
| subagent 需项目级定义 | bootstrap 投影 `harness-*.md` 七套角色 |
| 无平台原生模型路由 | 继承主 Agent model；如需手动指定由用户决定 |
| 连续自治循环非原生 | `continuous_mode` opt-in；其它走 `HANDOFF.md` 链接多会话 |

### Claude Code

| Claude 限制 | 缓解 |
| --- | --- |
| 无内置连续循环 | HANDOFF + DISPATCH-TRACK 跨会话接力（见 `claude-continuous-loop.md`） |
| 子 agent 仅 `generalPurpose` 一类 | `.agents/agents/<role>.md` 作 prompt 正文，由 prompt 区分角色 |
| 原生 plan 工具会写 `~/.claude/plans/` 脱管 | 在 `CLAUDE.md` / `AGENTS.md` 中添加禁止规则说明 |
| hooks 需用户自行配置 | 手动在 `settings.json` 中配置（可选） |
| 无独立 `shell` / `ci-investigator` task | 通用任务用 `generalPurpose`；CI 调查降级为 `generalPurpose readonly`（见 `capability-matrix.yaml`） |
| 项目级 skill 需投影到 `.claude/skills/` | `harness-project.sh project --platform claude` 自动从共享层 mirror |

### Trae

| Trae 限制 | 缓解 |
| --- | --- |
| 平台适配器为骨架，能力未完全定义 | 走 `orchestration` skill；待平台演进后补 capability |
| hooks 机制与 Cursor / Claude 不一致 | 用户自行配置（可选） |

---

## 自检清单（非阻塞）

| 平台 | 预检文件 |
| --- | --- |
| **Cursor** | `platform/cursor/.cursor/CURSOR-PRECHECK.md` |
| **Claude Code** | `platform/claude/README.md` § Hooks + 本文件「Claude 限制与缓解」表 |
| **Trae** | `platform/trae/README.md`（骨架） |

通用 harness 文档验证见 `scripts/harness-check.sh`。
