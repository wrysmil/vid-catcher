# Harness 能力注册表（单一真相源）

命名：`<domain>.<name>`，全小写，连字符分词。parity 审计见各 `platform/*/capability-matrix.yaml`。

## 完整性校验

新增 capability 时，必须同步更新：
- 本文件（registry.md）
- `platform/cursor/capability-matrix.yaml`
- `platform/claude/capability-matrix.yaml`

校验命令：`grep -c "### " core/capabilities/registry.md` 应等于各 YAML 中 `capabilities:` 下的 key 数量。

---

### routing.stage-gate

- **Requires:** 用户触发设计/计划/决策阶段
- **Produces:** spec/plan/decision 产物 + `## Next`
- **Forbidden:** 同轮改业务代码、派发 worker
- **Degraded:** 无

### routing.harness-declare

- **Requires:** 每个任务
- **Produces:** 首句 `「Harness：…」` + 可选 `Skills:`
- **Forbidden:** 无声明即交付
- **Degraded:** 无

### orchestration.dispatch

- **Requires:** 已批准 plan；routing 判定多 task 实现
- **Produces:** execution-log、DISPATCH-TRACK、代码变更
- **Forbidden:** 未过 plan 门禁派发
- **Parameters:** 见 `core/orchestration/config.defaults.yaml`
- **Degraded:** generic 平台顺序 SpawnWorker

### orchestration.leader

- **Requires:** 编排会话
- **Produces:** 路由判定、派发、整合、尾盘落盘
- **Forbidden:** Leader 写业务代码（小改动除外）；自动 push
- **Degraded:** 无

### orchestration.parallel-wu

- **Requires:** GROUP 内无依赖 WU；文件不相交
- **Produces:** 并行 worker 返回
- **Forbidden:** 同文件并行；超 `max_parallel`（硬顶 5）
- **Parameters:** `max_parallel` 默认 3
- **Degraded:** 顺序 SpawnWorker；track 记 `parallel degraded, sequential`

### orchestration.dispatch-track

- **Requires:** 并行编排
- **Produces:** `tracking/DISPATCH-TRACK-*.md` append-only
- **Forbidden:** 改删历史行
- **Degraded:** 无

### orchestration.worktree-sandbox

- **Requires:** 将委派写代码类 worker
- **Produces:** WORKTREE-INIT/CLOSE 条目
- **Forbidden:** 有委派却跳过 INIT；无委派仍 INIT
- **Degraded:** 无（脚本共用）

### orchestration.collective-closeout

- **Requires:** GROUP 全部 WU 返回
- **Produces:** collective-test + code-review 产物
- **Forbidden:** 末 WU 返回即声称完成
- **Degraded:** 无

### orchestration.continuous-loop

- **Requires:** 用户 opt-in
- **Produces:** HANDOFF 衔接
- **Forbidden:** 默认启用
- **Degraded:** Claude/generic 多会话人工 HANDOFF

### roles.coder

- **Requires:** 代码类 WU
- **Produces:** 实现 + 单测 + 轻量审查 + 自检
- **Forbidden:** E2E；改 plan/tracking
- **Degraded:** 无

### roles.implementer

- **Requires:** docs/chore/config WU
- **Produces:** 限定文件变更
- **Forbidden:** 业务逻辑大改
- **Degraded:** 无

### roles.reviewer

- **Requires:** 尾盘或独立审查
- **Produces:** 审查结论（Leader 落盘）
- **Forbidden:** 与实现同实例；worker 内 Write reviews/
- **Degraded:** 无

### roles.test-engineer

- **Requires:** test/e2e WU
- **Produces:** 测试资产变更
- **Forbidden:** 改生产业务逻辑（非测试辅助）
- **Degraded:** 无

### roles.smoke-tester

- **Requires:** smoke WU
- **Produces:** `.ai-runtime-artifacts/verifications/*-smoke-report.md` + `screenshots/`
- **Forbidden:** 写测试代码、改业务实现、自选浏览器 skill
- **Degraded:** 无（浏览器依赖属前置 preflight，由 Leader 校验）

### roles.explorer

- **Requires:** 只读探查 WU
- **Produces:** 探查摘要
- **Forbidden:** 写业务代码
- **Degraded:** 无

### roles.debugger

- **Requires:** 缺陷调查 WU
- **Produces:** 根因与修复建议/变更
- **Forbidden:** 跳过 systematic-debugging
- **Degraded:** 无

### roles.web-investigator

- **Requires:** 调研 WU
- **Produces:** research 产物
- **Forbidden:** 无
- **Degraded:** 无

### artifacts.runtime-layout

- **Requires:** 非小改动任务
- **Produces:** `.ai-runtime-artifacts/` 树与 FM
- **Forbidden:** 路径自创
- **Degraded:** 无

### skills.stage-load

- **Requires:** routing Route 列含 stage skill
- **Produces:** 按 skill 流程交付
- **Forbidden:** 未 Load 即写产物
- **Degraded:** 无

### interaction.structured-ask

- **Requires:** 设计阶段澄清
- **Produces:** 用户选择
- **Forbidden:** 一次多问
- **Degraded:** Claude 对话式单选

### hooks.session-lifecycle

- **Requires:** 用户配置 hook
- **Produces:** 本地 hook 日志
- **Forbidden:** 失败阻断主路径
- **Degraded:** Claude manual

### artifacts.verification-lite

- **Requires:** Tier 1 Leader 直做完成
- **Produces:** `verifications/*-verification-lite.md`
- **Forbidden:** 替代 Tier 2+ execution-log / collective-test
- **Degraded:** 无

### git.worktree-script

- **Requires:** 将委派写代码类 worker
- **Produces:** worktree 创建/清理脚本执行
- **Forbidden:** 有委派却跳过 worktree 初始化
- **Degraded:** generic 手动 git worktree

### verification.collective-test

- **Requires:** GROUP 全部 WU 返回
- **Produces:** `verifications/*-collective-test.md`
- **Forbidden:** 未运行 `project.verification.md` 命令即声称 PASS
- **Degraded:** 无

### verification.collective-review

- **Requires:** GROUP 全部 WU 返回 + 集体测试 PASS
- **Produces:** `reviews/*-code-review.md`
- **Forbidden:** reviewer 与实现同实例；worker 内 Write reviews/
- **Degraded:** 无

### verification.before-completion

- **Requires:** 任何完成声明
- **Produces:** 验证证据（verification-lite 或 collective-test）
- **Forbidden:** 无新鲜验证证据即声称完成（铁律）
- **Degraded:** 无

### verification.fix-loop

- **Requires:** 集体审查 BLOCK 或验证 FAIL
- **Produces:** review-fix WU + 重新验证
- **Forbidden:** 跳过修复直接声称完成
- **Degraded:** 无
