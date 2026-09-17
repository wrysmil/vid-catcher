# 常用命令

组织级日常片段见下文「按场景」；分支含义与合流顺序见 `workflow.md`。

## 每日开始工作

```bash
git checkout develop
git pull origin develop
git checkout -b task/my-task-name     # 或 feature/…、temp/…
```

## 日常提交

```bash
git add .
git status
git commit -m "feat(module): 具体描述"
git push -u origin task/my-task-name   # 首次可 -u 建立跟踪
```

## 提交前同步 develop（推荐 rebase）

```bash
git fetch origin
git rebase origin/develop
# 若有冲突：编辑文件后
git add .
git rebase --continue
# 或中止：git rebase --abort
```

## feature / task 完成后（推送并开 MR）

```bash
git push origin feature/my-feature
# 在平台上向 develop 发起 MR/PR
```

## bugfix（从 main，合入 main + develop）

```bash
git checkout main
git pull origin main
git checkout -b bugfix/v2.3.12-login-token-expire
# … 修复 …
git add .
git commit -m "fix(auth): 修复登录 token 过期时间计算错误"
git push -u origin bugfix/v2.3.12-login-token-expire
# 分别向 main、develop 发起 MR（顺序以团队规定为准）
# 在 main 上打标签（版本负责人；标签名勿与同名的远程分支冲突）
git checkout main
git pull origin main
git tag -a v2.3.12 -m "bugfix: 修复登录 token 过期问题"
git push origin v2.3.12
git branch -d bugfix/v2.3.12-login-token-expire
git push origin --delete bugfix/v2.3.12-login-token-expire
```

## 提测分支 test/v*（示例）

```bash
git checkout develop
git pull origin develop
git checkout -b test/v2.4.0
# 部署测试；此阶段以修 bug 为主
# 测试通过后 MR → main，打 tag；再将 test 上修复 merge 回 develop，最后删除 test 分支
```

## temp 验证（统一用 temp/*）

```bash
git checkout develop
git pull origin develop
git checkout -b temp/try-redis-cache
# … 验证 …
# 保留则 MR → develop；放弃则：
git checkout develop
git branch -D temp/try-redis-cache
git push origin --delete temp/try-redis-cache
```

## 合并后清理

```bash
git checkout develop
git pull origin develop
git branch -d task/my-task-name
git push origin --delete task/my-task-name
```

## 紧急回滚（受保护分支）

```bash
git revert <commit-hash>
git push origin develop    # 或 main，视分支而定
# 禁止在 main/develop 上用 reset --hard 做「团队回滚」
```

撤销**错误的合并提交**：

```bash
git checkout develop
git revert -m 1 <merge-commit-hash>
git push origin develop
```

---

## 入门

```bash
git config --global user.name "你的姓名"
git config --global user.email "你的@邮箱.com"
git init
git clone <仓库 URL>
```

## 查看变更

```bash
git diff                    # 未暂存变更
git diff --staged           # 已暂存变更
git log --oneline -10       # 最近提交
git log --graph --all       # 图形化历史
git show commit-hash        # 指定提交
git blame file.txt          # 每行最后修改者
```

## 暂存

```bash
git add -p                  # 交互式暂存（部分文件）
git restore --staged file   # 取消暂存
git restore file            # 丢弃工作区修改
git reset                   # 全部取消暂存
```

## 贮藏

```bash
git stash                   # 临时保存工作
git stash -m "wip: feature" # 带说明
git stash list              # 贮藏列表
git stash pop               # 应用并删除
git stash apply             # 应用但保留贮藏
git stash drop              # 删除不应用
```

## 标签

```bash
git tag                     # 列出标签
git tag v1.0.0              # 轻量标签
git tag -a v1.0.0 -m "msg"  # 附注标签
git push origin v1.0.0      # 推送单个标签
git push --tags             # 推送全部标签
git tag -d v1.0.0           # 删除本地标签
git push origin --delete v1.0.0  # 删除远程标签
```

## 远程

```bash
git remote -v               # 列出远程
git remote add origin URL   # 添加远程
git fetch origin            # 下载不合并
git push -u origin branch   # 推送并设置上游
git push --force-with-lease # 安全强推（仅允许的个人功能分支）
```

## 撤销（注意受保护分支策略）

```bash
git reset --soft HEAD~1     # 撤销提交，保留暂存（勿用于 main/develop 协作回滚）
git reset --mixed HEAD~1    # 撤销提交，保留未暂存
git reset --hard HEAD~1     # 撤销提交并丢弃变更（仅限个人分支/本地场景）
git revert commit-hash      # 新建反向提交（主干推荐）
git checkout -- file        # 丢弃文件变更（旧写法）
git restore file            # 丢弃文件变更（新写法）
```

## cherry-pick

```bash
git cherry-pick commit-hash     # 应用指定提交
git cherry-pick -n commit-hash  # 应用但不自动提交
git cherry-pick --abort         # 中止进行中的操作
```

## 清理

```bash
git clean -n                # 预览将删除的内容
git clean -f                # 删除未跟踪文件
git clean -fd               # 删除未跟踪文件与目录
git clean -fdx              # 同时删除被忽略文件
```

## 子模块

```bash
git submodule add URL path  # 添加子模块
git submodule update --init # 克隆后初始化
git clone --recurse-submodules URL  # 带子模块克隆
git submodule update --remote       # 更新到远程最新
```

## 别名（写入 ~/.gitconfig）

```ini
[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    lg = log --oneline --graph --all
    amend = commit --amend --no-edit
    unstage = reset HEAD --
```
