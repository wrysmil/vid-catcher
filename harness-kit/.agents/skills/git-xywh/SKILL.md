---
name: git-xywh
slug: git-xywh
version: 1.0.9
description: "组织级 Git 工作流：三主干（main / test / develop）、五类临时分支（feature / task / temp / bugfix / test）、多环境隔离、Angular 提交与 MR 流程；并涵盖日常安全操作（合并、变基、冲突、恢复）。在以下情况使用：（1）任务涉及上述分支、提测线、热修或版本标签；（2）需要写符合规范的提交说明或走合并请求；（3）需要避免误操作受保护分支或污染历史。"
changelog: 审查改造：slug 与 clawhub 统一、跨平台命令说明、workflow 与 SKILL 去重、密钥与子模块补充
homepage: https://clawic.com/skills/git
metadata: {"clawdbot":{"emoji":"📚","requires":{"bins":["git"]},"os":["linux","darwin","win32"]}}
---

## 何时使用

当任务涉及本组织的 **`main` / `test` / `develop`**、**`feature` / `task` / `temp` / `bugfix` / `test/v*`** 分支、**合并请求**、**版本号与标签**、或需要**安全地**合并、变基、解决冲突、恢复历史时使用。本技能无状态，凡工作包含上述 Git 协作，默认应套用。

**安装与反馈时的对外标识以 `slug`（`git-xywh`）为准**；YAML 中的 `name: Git` 仅为人类可读名称，与包管理器检索字段可能不同。

## 必读约束（代理与成员）

1. 不向 `main`、`develop` 直推个人开发结果 — 走 MR/PR。  
2. 不在公共受保护分支上 `git push --force`；允许时个人分支用 `--force-with-lease`。  
3. `main` / `develop` 协作回滚用 `git revert`，不用 `reset --hard` 改写已发布历史。  
4. `bugfix/*` 从 `main` 拉出，且须合入 `main` 与 `develop`。  
5. 含密钥或凭据的提交即使事后删除提交记录，仍可能泄露 — 须**轮换密钥**并按平台流程联系管理员清理历史（见 `workflow.md` §14）。

## 分支类型速判（决策树）

- **生产紧急缺陷** → 从 `main` 建 `bugfix/*`，再分别合入 `main` 与 `develop`。  
- **已冻结/提测的版本线** → `test/v*`，以修缺陷为主，通过后进 `main` 并回合 `develop`。  
- **大模块、长周期、多子分支** → `feature/*`（自 `develop`）。  
- **常规需求** → `task/*`（自 `develop`）。  
- **短探索、试错** → `temp/*`（自 `develop`）；可废弃或转正为 feature/task。  
- 长期「测试环境集成分支」若团队命名为 `test`，以远端保护规则与发布流程为准，勿与提测线 `test/v*` 混淆。

## 速查

| 主题 | 文件 |
|-------|------|
| **组织工作流（分支模型与合流顺序）** | `workflow.md` |
| 常用命令（含每日/提测/热修片段） | `commands.md` |
| 进阶操作 | `advanced.md` |
| 分支陷阱（结合本模型） | `branching.md` |
| 冲突处理 | `conflicts.md` |
| 历史与恢复 | `history.md` |
| 协作与受保护分支 | `collaboration.md` |

| 易混辨析 | 说明 |
|----------|------|
| **`test` 主干 / `test/v*` 分支 / 提交类型 `test`** | 主干 `test` = 测试环境长期分支；`test/v2.4.0` 等 = 某次提测版本线；Angular 里 **`test`** 表示**测试代码/用例**的提交类型，三者语义不同。 |

## 核心规则（组织）

1. **不向 `main`、`develop` 直推个人开发结果** — 通过 MR/PR 合入；具体权限以远程保护规则为准。
2. **不在公共受保护分支上 `git push --force`** — 个人功能分支若需更新远程，优先 `--force-with-lease`，且须符合团队规定。
3. **`main` / `develop` 上不以 `reset --hard` 做协作回滚** — 使用 `git revert`（合并提交用 `revert -m 1`）。个人分支与本地未推送整理仍可用 `reset`/`rebase`。
4. **热修复 `bugfix/*` 从 `main` 拉出，且须合入 `main` 与 `develop`** — 避免只修生产、开发线再现缺陷。
5. **提测分支 `test/v*` 上以修缺陷为主** — 测试通过后合 `main`、打标签，并将修复回合 `develop`（见 `workflow.md`）。
6. **临时验证分支统一使用 `temp/*`**。
7. **提交前将功能分支与 `origin/develop` 对齐** — 推荐 `git fetch` 后 `git rebase origin/develop`（冲突则解决后继续）。
8. **MR 合并后删除对应功能分支** — 本地与远程。

## 通用规则（仍适用）

- **尽早、频繁提交** — 小提交更易审查、回滚与二分定位。
- **首行提交说明简洁** — 建议不超过约 72 字符；类型与范围见下文。
- **大文件与密钥** — 单文件大于约 **10MB** 时用 Git LFS 或外部存储；**禁止**提交密钥与凭据（见 `workflow.md` 中 ignore 示例）。

## 提交规范（Angular）

- **格式**：`<类型>(<范围>): <主题>`，可加正文与页脚（如 `Closes #142`）。
- **类型示例**：`feat`、`fix`、`docs`、`style`、`refactor`、`test`、`chore`、`perf`。
- **范围示例**：`user`、`order`、`api`、`dashboard`、`model`（与仓库模块划分一致）。

**正面示例：**

```
feat(user): 添加用户头像上传功能

- 支持 jpg/png，最大 5MB
- 集成 OSS

Closes #142
```

```
fix(order): 修复金额计算精度丢失问题
```

**反面示例（应避免）：** `update`、`修改了一些东西`、`fix bug`、`1111`、`暂存先提交` 等无信息量说明。

## 推送与强推

- 功能分支若必须覆盖远程历史，使用 **`git push --force-with-lease`**，且仅限**允许强推**的个人分支。
- 推送被拒时先 **`git fetch`**，再与 `develop` 对齐后推送。
- **不要**对 `main` 及组织规定的受保护分支强推。

## 冲突处理

- 解决后确认无残留冲突标记：在仓库根目录执行 **`git grep -nE '^(<{7}|={7}|>{7})'`**（随 Git 自带，Windows/macOS/Linux 一致）；或在 **Git Bash** 下使用 `grep -rE '<<<|>>>|===' .`；亦可在 IDE 中全局搜索 `<<<<<<<`。
- 合并或变基完成前确保能构建、测试通过。
- 过复杂时可 `git merge --abort` 或 `git rebase --abort`，再换策略（见 `conflicts.md`）。

## 分支卫生

- 合并后：`git branch -d <分支>`，并 `git push origin --delete <分支>`（若适用）。
- 定期 `git fetch --prune` 清理已删除的远程分支引用。
- 推送前可用 `git rebase -i` 整理仅属于本分支、且团队允许压平的提交。

## 安全清单（破坏性操作前）

在执行 `reset --hard`、变基、可能改写历史的强推前：

- [ ] 是否为**他人依赖的共享分支**？→ 不要改写其历史。
- [ ] 是否有未提交更改？→ 先提交或 `stash`。
- [ ] 当前分支是否正确？→ `git branch` / `git status`。
- [ ] 是否已 `fetch`？→ 避免基于过时远程操作。

## 常见陷阱

- **user.email / user.name** — 提交前核对 `git config`。
- **空目录** — Git 不跟踪空目录，可放 `.gitkeep`。
- **子模块** — 克隆使用 `--recurse-submodules`。
- **游离 HEAD** — `git switch -` 返回上一分支。
- **stash pop 冲突** — 暂存可能被移除；需要保留时用 `stash apply`。
- **大小写** — Windows/macOS 与 Linux 不一致易导致 CI 失败。

## 恢复与调试（摘要）

- 撤销最近一次提交保留改动：`git reset --soft HEAD~1`（**仅限未破坏协作规则的场景**）。
- 丢弃工作区文件改动：`git restore <文件>`。
- 查找丢失提交：`git reflog`。
- 二分定位：`git bisect`（见 `advanced.md`）。

## 速记

```bash
git status -sb
git log --oneline -5
git fetch origin
git rebase origin/develop    # 在功能分支上同步开发主线时常用
git branch -vv
git stash list
```

## 相关技能

用户确认后可用 `clawhub install <slug>` 安装（本技能示例：`clawhub install git-xywh`）：

- `gitlab` — GitLab CI/CD 与合并请求
- `docker` — 容器化工作流
- `code` — 代码质量与最佳实践

## 反馈

- 若觉得有用：`clawhub star git-xywh`
- 保持更新：`clawhub sync`
