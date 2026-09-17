# AGENTS.md（Harness 仓库根覆盖层）

> 本文件是 **harness-kit 仓库根** 的 `AGENTS.md`。  
> 详细入口与跨平台规则见 `harness-kit/core/routing.md`。  
> AI 入口顺序：1. 本文件 → 2. `harness-kit/core/routing.md` → 3. 平台适配器入口。

## 仓库性质

本仓库是 **harness-kit 自身**（脚手架 + 模板 + 适配器 + 脚本），**不是**部署目标。业务项目通过 `harness-kit/scripts/install-ai-skills.sh` 接入。

## AI 入口（按序读取）

1. 本文件（仓库根覆盖层）
2. `harness-kit/core/routing.md`（路由判定 / 阶段门禁 / 按判定加载）
3. `harness-kit/core/artifacts.md`（产物规范）
4. `harness-kit/core/artifacts.md`（产物规范）
5. 平台适配器入口（`platform/claude/README.md` / `platform/cursor/README.md` / `platform/trae/README.md`）

## 强制声明

每个任务首句 `「Harness：<route 或 "Tier 0 小改动" | "Tier 1 Leader 直做">」`；stage skill / Tier 1+ 次行 `Skills: <slug>@<path> loaded|skipped`。细则见 `routing.md` § 阶段指定 skill 必用。

## 产物落盘（强制）

**所有 AI 过程产物必须写入 `.ai-runtime-artifacts/` 对应子目录，禁止写入其他位置。**

| 产物类型 | 目录 |
| --- | --- |
| spec / 方案 | `.ai-runtime-artifacts/specs/` |
| plan / 计划 | `.ai-runtime-artifacts/plans/` |
| dispatch / 调度 | `.ai-runtime-artifacts/plans/`（同 stem 的 `*-dispatch.md`） |
| verification / 验证 | `.ai-runtime-artifacts/verifications/` |
| collective-test / 集体测试 | `.ai-runtime-artifacts/verifications/*-collective-test.md` |
| review / 审查 | `.ai-runtime-artifacts/reviews/` |
| code-review / 代码审查 | `.ai-runtime-artifacts/reviews/*-code-review.md` |
| execution-log / 执行日志 | `.ai-runtime-artifacts/execution-logs/` |
| dispatch-track / 追踪 | `.ai-runtime-artifacts/execution-logs/tracking/` |
| decision / 决策 | `.ai-runtime-artifacts/decisions/` |
| retro / 复盘 | `.ai-runtime-artifacts/retros/` |
| research / 调研 | `.ai-runtime-artifacts/research/` |

**禁止：**
- 把产物写到 `docs/`、`项目根目录`、或其他任意位置
- 把 plan 写到平台私有目录（如 `~/.claude/plans/`）
- 用 `docs/superpowers/` 代替 `.ai-runtime-artifacts/`

**例外：** harness-kit 仓库自身（`.gitignore` 排除 `.ai-runtime-artifacts/`）的 closeout 示例可放 `docs/runtime/closeouts/`。

## 沟通语言

对用户回复、子 Agent 派发、产物摘要、验收口径全部使用**中文**（代码标识符、路径、命令、API 名、固定段键名保留英文）。细则见 `routing.md` § 沟通语言。

## 参考资料索引

**检查清单已内嵌到各 Agent 定义文件中**，无需外部引用。各 Agent 的 `.md` 文件包含完整的检查表（性能反模式、日志规范、安全检查、完成定义等）。

**违反：** 未执行检查即声称完成 → 无效。

