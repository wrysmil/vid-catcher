---
artifact: runbook
route: harness-init
skills:
  - explore
  - planner
source:
  - harness-kit/core/harness.md
  - harness-kit/init/templates/project.profile.md
  - harness-kit/init/templates/context-map.md
  - harness-kit/init/templates/project.verification.md
  - harness-kit/init/templates/project.git.md
created_at: 2026-05-14
---

# Project Profiler Prompt

你正在为一个新项目初始化 Agent Harness。目标是读取当前仓库，生成项目画像、上下文地图和验证画像。

## 输入

请读取：

1. `README.md`
2. `package.json`
3. lockfile / workspace 配置
4. 顶层目录结构
5. `src/`、`main/`、`preload/`、`apps/`、`packages/`、`docs/` 等存在的关键目录
6. 已有构建、测试、lint、CI 配置
7. Git 相关：`.husky/`、`commitlint`、`.gitlab-ci.yml`、`.github/workflows`、`CONTRIBUTING.md` 等
8. 现有项目文档

## 输出文件

以 `harness-kit/init/templates/` 中同名文件为**章节骨架**（保留「推断项」「待确认项」等节），创建或更新：

1. `harness-kit/project.profile.md`
2. `harness-kit/context-map.md`
3. `harness-kit/project.verification.md`
4. `harness-kit/project.git.md`（仅项目相对 `git-xywh` 的差异；不复制组织 Git 全文）

## 填充平台入口背景

用 `project.profile.md` 的「项目身份」与「技术栈」写成 2–4 句摘要，替换根目录 `AGENTS.md` 中的 `{{PROJECT_BACKGROUND}}`。

## 要求

- 不修改业务代码。
- 不读取 secret、token、provider key 或本机私有配置。
- 对无法确认的信息，写入“待确认项”。
- 对基于文件结构推断的信息，写入“推断项”。
- 保持内容简洁，面向 AI 和工程师共同阅读。
- 最后运行 `bash harness-kit/scripts/harness-check.sh`。

## 输出摘要

完成后在回复中说明：

- 读取了哪些关键文件。
- 生成或更新了哪些 Harness 文件。
- 哪些信息是推断项。
- 哪些信息需要人工确认。
- `harness-check` 是否通过。
- **Claude 平台层实际生成文件清单**（若适用平台为 Claude）：rules 文件名、skills 镜像数、hooks 脚本与 `settings.json.example` 是否存在；缺一即报告并补投影（`bash harness-kit/scripts/harness-project.sh project --platform claude --force`）。
