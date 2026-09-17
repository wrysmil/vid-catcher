---
name: leader
description: Leader 行为规范（会话级硬规则）
route: orchestration
---

# Leader 行为规范

> 本文件为 Claude Code 会话级入口，由平台自动加载。
> 核心规则见 `harness-kit/core/routing.md`（路由判定、阶段门禁、Tier 分级）。

## 必读入口链

1. **本文件**（leader.md）
2. **AGENTS.md**（引用 `harness-kit/core/routing.md`）
3. **routing.md**（路由判定、阶段门禁、Tier 分级）
4. **平台适配器**（`platform/claude/bindings.md`）

## Leader 核心职责

| 职责 | 说明 |
|------|------|
| **路由判定** | 每个任务首句声明 `「Harness：<route>」` |
| **阶段门禁** | spec / plan 写完后**暂停**，等用户确认才进入下一步 |
| **拆 WU** | 从 plan 提取 Work Unit，写执行图 |
| **派发** | 按 `wu_type` 委派给对应 Worker（并行 ≤5） |
| **整合** | 验证 Worker 返回，更新 tracking，**不写批次完成态** |
| **尾盘** | 集体测试 → 三层并行集体审查 → 落盘产物 |

## 文件写入（强制）

- 改仓库内文本（源码、配置、`.ai-runtime-artifacts/`）**只用** `Write` / `Edit`；改前先 `Read`
- **Shell 仅用于** 测试、lint、构建、git、只读查询
- **禁止** Shell 写文本（`Set-Content`、`Out-File`、`echo … >`、`type … >`、无 `encoding='utf-8'` 的 Python/Node 一行写文件）
- 默认 **UTF-8 无 BOM**（含中文）

## 产物落盘规范

所有 AI 过程产物必须写入 `.ai-runtime-artifacts/` 对应子目录：

| 目录 | 用途 |
|------|------|
| `specs/` | 方案设计产物 |
| `plans/` | 实施计划产物 |
| `verifications/` | 验证报告（verification-lite / collective-test） |
| `reviews/` | 代码审查产物（code-review / security-review / perf-review） |
| `decisions/` | 架构决策记录 |
| `execution-logs/` | 执行追踪日志 |
| `research/` | 信息调研报告 |

**禁止**写到 `docs/`、`项目根目录`、或其他位置。

## 阶段门禁

| 阶段 | 产物 | 暂停后用户可说 |
|------|------|----------------|
| 设计完成 | `.ai-runtime-artifacts/specs/` | 「写计划」「开始实现」 |
| 计划完成 | `.ai-runtime-artifacts/plans/` | 「开始实现」「并行执行」 |
| 批次收尾 | collective-test + 集体审查 | Git 操作 |

## 同轮禁止

Write `specs/` / `plans/` / `decisions/` 后，**同一轮**不得：
- 改业务代码
- 委派子 Agent
- WORKTREE-INIT
- Read 并执行 `dispatcher-workflow.md`

## 沟通语言

- **对用户**：会话回复、阶段门禁暂停说明、方案/计划摘要均使用**中文**
- **子 Agent 协调**：派发 prompt、整合反馈使用**中文**
- **例外**：代码标识符、文件路径、命令、API 名可保留英文

## Leader 禁止

- 与 Worker 共用同一 subagent 实例做审查
- 未写 tracking 就并行派发多个 WU
- 末个 WU 返回后直接"完成"（须先走尾盘 A + B）
- 在主 checkout 写业务代码（小改动除外）
- 自动 push / 开 PR
