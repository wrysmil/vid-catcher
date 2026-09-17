---
generated_at: YYYY-MM-DD
generator: harness-init
org_skill: git-xywh
---

# Project Git — <project-name>

本文件只记录**相对组织 Git 规范（`git-xywh` skill）的差异**与**本项目约束**。分支模型、MR 流程、Angular 提交格式全文见 skill，不在此重复。

> 骨架来源：`harness-kit/init/templates/project.git.md`。接入项目时由 `project-profiler` 生成并替换占位；勿手抄其他项目内容。

## 组织基线（默认）

- **Skill**：`git-xywh`
- **何时 invoke**：建分支、提交、rebase、开 MR/PR、热修、合流、打标签、历史恢复；Cursor 多 task 时 **WORKTREE-INIT/CLOSE** 亦须先 Load
- **执行角色**：**Leader / 主 Agent**；子 Agent 默认不 `git commit` / `push`

## 本项目差异（delta）

| 项 | 值 |
| --- | --- |
| 默认主干 | <!-- main / master / develop；受保护分支列表 --> |
| 组织模型 | 默认遵循 `git-xywh`；若本项目偏离，在下表写明 |
| 当前工作分支 | <!-- 可选；profiler 刷新 --> |
| 提交格式 | <!-- commitlint / Angular+中文 / 无约束 --> |
| 提交前检查 | <!-- husky、lint-staged、CI pre-commit --> |
| MR / PR 平台 | <!-- GitHub / GitLab / 其他 + workflow 路径 --> |
| Harness 脚手架提交 | 类型可用 `feat`/`chore`/`docs` 等；**标题与正文须中文**（如 `chore(harness-kit): 更新编排文档`），与业务 commit 分开 |
| Harness 执行沙箱 | 仓库外 `<repo-parent>/.harness-worktrees/<repo-basename>/wt-<dispatch-stem>/`；`git worktree add -b harness/wt-<stem> <path> <base>`；见 `docs/superpowers/specs/2026-05-29-git-worktree-isolation-design.md` |
| Harness push/PR | Leader **不**自动 push / 开 PR；须**用户确认**后再按 `git-xywh` 执行 |

## 如何调用 git-xywh

| 环境 | 做法 |
| --- | --- |
| Cursor / 支持 Skill 工具 | **先** `invoke` / 加载 skill **`git-xywh`**，再读本文件 |
| 无 Skill 工具 | Read `~/.cursor/skills/git-xywh/SKILL.md`（或 `~/.agents/skills/` 下同路径） |
| 安装检查 | `bash harness-kit/scripts/install-ai-skills.sh` 会输出 `ok:` 或 `missing:` |

详见 `routing.md` § Git 协作。

## AI 执行约束

1. 提交 / 分支 / worktree 操作前：**已加载 `git-xywh` skill 正文** + 读本文件（仅 delta）。
2. 禁止（除非用户明确要求）：向受保护主干直推；公共分支 force push；子 Agent 擅自 commit。
3. 用户说「帮我提交」：Leader 声明 `「Harness：git-xywh + project.git.md」` 后执行。
4. 委派子 Agent（`.agents/agents/`）时：业务代码在 **worktree_path**；不派子 Agent 则在主 checkout；编排产物始终在主 checkout（见 worktree spec）。

## 待确认项

- <!-- 远程保护分支、是否允许 AI push、MR 必填审查人 -->

## 推断项

- <!-- 基于 .github/workflows、.gitlab-ci.yml、.husky、commitlint 的推断 -->
