# Trae 平台适配器

第三参考实现：Trae Agent 并行 + core 编排语义。

## 接入

1. 根目录 `AGENTS.md`
2. 投影 skill：`bash harness-kit/scripts/harness-project.sh project`（含 `orchestration` skill）
3. 多 task 实现：Load **`orchestration`** → `core/orchestration/dispatcher-workflow.md`

## 平台检测

Trae 工作区 → `platform: trae`

## 与 Claude/Cursor 差异

| 能力 | 状态 |
| --- | --- |
| `interaction.structured-ask` | supported — Task 工具 |
| `orchestration.parallel-wu` | supported — max 3 并行 |
| `orchestration.continuous-loop` | manual — 多会话 HANDOFF |

parity 全表：`capability-matrix.yaml`。绑定：`bindings.md`。

## 目录结构

```
platform/trae/
├── bindings.md                 # 原语 → Trae 绑定映射
├── capability-matrix.yaml      # 26 项能力状态
├── VENDOR.md                   # 上游来源说明
├── README.md                   # 本文件
└── .trae/
    ├── rules/
    │   ├── ai-entry.md         # 统一入口
    │   └── trae-subagent-routing.md  # 子 Agent 路由
    ├── TRAE-PRECHECK.md        # 编排自检清单
    └── config.defaults.yaml    # 配置覆盖
```

## 关键文档

| 文档 | 用途 |
| --- | --- |
| `../../core/orchestration/dispatcher-workflow.md` | 编排唯一步骤源 |
| `bindings.md` | Trae 原语映射 |
| `capability-matrix.yaml` | parity 审计 |
| `.trae/rules/ai-entry.md` | Trae 入口规则 |
| `.trae/rules/trae-subagent-routing.md` | 子 Agent 路由 |
| `../../core/routing.md` | 路由权威 |

## 共享层

Trae 引用 `.agents/` 中的共享 skill 和 agent manifest：

- `.agents/skills/orchestration/SKILL.md`
- `.agents/agents/coder.md`
- `.agents/agents/implementer.md`
- `.agents/agents/reviewer.md`
- `.agents/agents/test-engineer.md`
- `.agents/agents/explorer.md`
- `.agents/agents/debugger.md`
- `.agents/agents/web-investigator.md`
