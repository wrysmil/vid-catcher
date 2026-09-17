---
generated_at: 2026-09-17
generator: harness-init
org_skill: git-xywh
---

# Project Git — VidCatcher

本文件只记录**相对组织 Git 规范（`git-xywh` skill）的差异**与**本项目约束**。分支模型、MR 流程、Angular 提交格式全文见 skill，不在此重复。

## 组织基线（默认）

- **Skill**：`git-xywh`
- **何时 invoke**：建分支、提交、rebase、开 MR/PR、热修、合流、打标签、历史恢复；Cursor 多 task 时 **WORKTREE-INIT/CLOSE** 亦须先 Load
- **执行角色**：**Leader / 主 Agent**；子 Agent 默认不 `git commit` / `push`

## 本项目差异（delta）

| 项 | 值 |
| --- | --- |
| 默认主干 | `main` |
| 组织模型 | 默认遵循 `git-xywh`；单人项目，暂无 MR 流程 |
| 当前工作分支 | `main` |
| 提交格式 | 无强制规范，建议语义化提交（feat/fix/chore/docs） |
| 提交前检查 | 无 husky/lint-staged |
| MR / PR 平台 | 单人项目，暂无远程协作 |
| Harness 脚手架提交 | 类型可用 `feat`/`chore`/`docs` 等；**标题与正文须中文**（如 `chore(harness-kit): 更新编排文档`），与业务 commit 分开 |
| Harness 执行沙箱 | 仓库外 `<repo-parent>/.harness-worktrees/<repo-basename>/wt-<dispatch-stem>/` |
| Harness push/PR | Leader **不**自动 push / 开 PR；须**用户确认**后再按 `git-xywh` 执行 |

## 如何调用 git-xywh

| 环境 | 做法 |
| --- | --- |
| Claude Code | **先** `Skill("git-xywh")` 或 `Read` harness-kit 中对应 skill，再读本文件 |
| 其他平台 | Read 对应路径下的 git-xywh skill 文件 |

详见 `routing.md` § Git 协作。

## AI 执行约束

1. 提交 / 分支 / worktree 操作前：**已加载 `git-xywh` skill 正文** + 读本文件（仅 delta）。
2. 禁止（除非用户明确要求）：force push；子 Agent 擅自 commit。
3. 用户说「帮我提交」：Leader 声明 `「Harness：git-xywh + project.git.md」` 后执行。
4. 委派子 Agent 时：业务代码在 **worktree_path**；不派子 Agent 则在主 checkout；编排产物始终在主 checkout。

## 待确认项

- 是否需要 commitlint 规范
- 是否需要 pre-commit hooks

## 推断项

- 无 CI/CD 配置（单人学习项目）
- 无远程保护分支
- 无 MR 必填审查人
