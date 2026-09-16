# 进阶操作

**说明**：下列命令适用于**个人功能分支**或本地整理。在 **`main` / `develop`** 上改写历史或「回滚发布」须遵守组织规则（通常使用 **`git revert`**，见 `workflow.md`）。

## 交互式变基

```bash
git rebase -i HEAD~5        # 编辑最近 5 个提交
# 须在「当前功能分支」上执行（不要检出到 develop 再执行）。以下命令整理的是「本分支相对 develop」的提交，不是编辑 develop 上的历史。
git rebase -i develop       # 等价于与 merge-base(develop) 之间范围的交互式变基；本组织常用集成分支名为 develop
```

编辑器中的指令：
- `pick` = 保留原样
- `reword` = 只改提交说明
- `squash` = 并入上一提交，保留说明
- `fixup` = 并入上一提交，丢弃本提交说明
- `drop` = 删除该提交

```bash
git rebase --continue       # 解决冲突后继续
git rebase --abort          # 取消并恢复
git rebase --skip           # 跳过当前有问题的提交
```

## 二分定位（查缺陷）

```bash
git bisect start
git bisect bad              # 当前提交有问题
git bisect good v1.0.0      # 已知正常版本

# Git 会检出中间提交。测试后执行：
git bisect good             # 此处无问题
git bisect bad              # 此处有问题
# 重复直到定位

git bisect reset            # 结束，回到原分支
```

自动化二分：
```bash
git bisect start HEAD v1.0.0
git bisect run ./test-script.sh   # 退出码 0 表示好，1 表示坏
```

## 工作树（并行工作）

```bash
git worktree add ../hotfix hotfix-branch   # 新目录检出某分支
git worktree add ../feature -b new-feature # 新建并检出分支
git worktree list                          # 列出所有工作树
git worktree remove ../hotfix              # 移除工作树
```

适用场景：
- 评审 PR 同时保留当前开发
- 在 main 上跑测试，同时在别的分支开发
- 对比不同版本行为

## reflog（恢复）

```bash
git reflog                  # 所有 HEAD 移动记录
git reflog show branch      # 某分支的历史
```

恢复示例：
```bash
# 变基搞砸之后
git reflog
# 下标 @{} 以你本地 git reflog 输出为准，勿照搬数字
git reset --hard HEAD@{5}   # 示例：回到某条 reflog 记录对应状态

# 恢复已删分支
git reflog
git branch recovered commit-hash

# 恢复误删的 stash（任选其一）
# A) Git Bash：git fsck --unreachable | grep commit
# B) 任意环境：git fsck --unreachable，在输出中查找可疑 commit，再用 git show <hash> 确认
```

## 稀疏检出（大仓库）

```bash
git sparse-checkout init --cone
git sparse-checkout set packages/my-app packages/shared
git sparse-checkout add packages/another
git sparse-checkout disable         # 再次完整检出
```

带稀疏检出的克隆：
```bash
git clone --filter=blob:none --sparse URL
cd repo
git sparse-checkout set path/to/need
```

## subtree 与 submodule

**Subtree**（把代码拷贝进本仓库）：
```bash
git subtree add --prefix=lib/shared URL main --squash
git subtree pull --prefix=lib/shared URL main --squash
git subtree push --prefix=lib/shared URL main
```

**Submodule**（指向某次提交）：
```bash
git submodule add URL path
git submodule update --init --recursive
git submodule update --remote
```

**安全提示**：子模块锁在**指定提交**；更新上游（`update --remote`）前应做**变更审查**，避免供应链被篡改的引用进入主仓库。

选 subtree：工作流更简单、更新不频繁  
选 submodule：依赖很大、独立发布周期

## 合并与变基

**合并**（保留历史，示例以集成分支 `develop` 为目标）：
```bash
git checkout develop
git merge feature           # 产生合并提交
git merge --no-ff feature   # 始终产生合并提交
```

**变基**（线性历史）：
```bash
git checkout feature
git rebase develop          # 把提交重放到 develop 之上
git checkout develop
git merge feature           # 快进合并
```

原则：仅对本地、未发布或团队允许改写的分支变基。**不要**变基他人依赖的共享分支；本组织中集成目标一般为 **`develop`**。

## 冲突解决工具

```bash
git mergetool               # 启动已配置的合并工具
git checkout --ours file    # 采用当前分支版本
git checkout --theirs file  # 采用并入侧版本
```

查看各阶段版本：
```bash
git show :1:file            # 共同祖先
git show :2:file            # 我方
git show :3:file            # 对方
```

## rerere（记住解决方式）

```bash
git config --global rerere.enabled true   # 记住冲突解决
git rerere forget file                    # 忘记某次错误解决
```
