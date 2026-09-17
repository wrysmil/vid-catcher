# 历史相关陷阱

## reset

- 在 **`main` / `develop` 等受保护分支上**，不要用 `reset --hard` 做**团队可见的回滚** — 请用 `revert`（见 `workflow.md`）。以下仍描述 `reset` 的通用行为与风险。
- `git reset --hard` 会**永久**丢失未提交更改 — 无法撤销
- `--hard` 与 `--soft` 与 `--mixed` — 各自移动的内容不同
- 对已推送提交做 reset = 历史分叉 — 需要强推
- 带未跟踪文件的 reset = 未跟踪文件仍存在 — 容易出乎意料

## revert

- revert 会创建**新**提交 — 不会删除原提交
- 对合并提交做 revert 需要 `-m 1` 或 `-m 2` — 否则报错
- 对 revert 再 revert = 重新应用更改 — 历史易混淆
- 对很旧的提交 revert 可能与后续提交冲突

## amend

- `--amend` 会改变 SHA — 修正后的提交是**另一条**提交
- 对已推送提交 amend = 与变基类似的问题
- 未暂存就 `--amend` = 只改提交说明
- 误在错误提交上 amend = 用 reflog 恢复

## reflog

- reflog 仅在**本地** — 不会与远程同步
- reflog 会过期（默认约 90 天）— 旧提交会消失
- `git gc` 可能在过期前就清理不可达提交
- 已删分支的 reflog 在 HEAD 的 reflog 里，不在分支 reflog

## cherry-pick

- cherry-pick 会生成新提交，SHA 不同
- 先 cherry-pick 再合并 = 历史中重复提交
- 对合并提交 cherry-pick 需要 `-m` 参数
- cherry-pick 冲突 = 与变基时同样方式解决

## blame

- `git blame` 显示的是最后修改，不是最初作者
- 加 `-w` 可忽略空白变更
- `git log -p 文件名` 显示该文件的完整变更历史
- 对移动过的代码 blame：重命名文件用 `git log --follow`
