---
name: AGENTS
description: Agent Harness 入口
---

# AGENTS.md

项目背景：**万能视频下载站（学习向）** — 本机/局域网学习项目，用 FastAPI 把 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 薄封装成网页版视频下载器，配 Vue 3 + Vite 前端，目标是理解「薄封装开源引擎 + 转化向前端」的开发方式。后端 Python（`backend/`，FastAPI + 线程池任务表），前端 Vue 3（`frontend/`，Vite 代理 `/api` 到 8000）。一期明确**无数据库、无鉴权、无真实支付**，页面上的总结 / 翻译 / 批量是占位；合规边界是只下载用户有权保存的公开内容，不碰 DRM 与大会员。

> 必读：`harness-kit/core/routing.md`（路由判定、阶段门禁、按判定加载）
> AI 入口顺序：1. 本文件 → 2. `harness-kit/core/routing.md` → 3. 平台适配器入口

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
| stack / 版本清单 | `.ai-runtime-artifacts/stack/` |
| contract / 接口契约 | `.ai-runtime-artifacts/contracts/` |

**禁止：**
- 把产物写到项目根目录、`frontend/`、`backend/` 或其他任意位置
- 把 plan 写到平台私有目录（如 `~/.claude/plans/`）
- 使用 Claude Code `EnterPlanMode` / `ExitPlanMode` 等原生 plan 工具（绕过 Harness 门禁）

## 沟通语言

对用户回复、子 Agent 派发、产物摘要、验收口径全部使用**中文**（代码标识符、路径、命令、API 名、固定段键名保留英文）。细则见 `routing.md` § 沟通语言。

## 项目特定约束

- **勿读、勿提交** `.env`、密钥、token、`.cursor/mcp.json`（含明文 API key）。
- `harness-kit/` 是脚手架，**勿当业务模块改**；项目差异写在 `harness-kit/project.*.md`。
- 不引入 DRM 破解、Cookie 盗用、绕过登录态的实现；站点改版导致解析失败时升级 `yt-dlp` 版本，**不要**自己写提取器。
- `frontend/dist/`、`backend/tmp_downloads/`、`backend/.venv/` 均为产物，不入仓。
