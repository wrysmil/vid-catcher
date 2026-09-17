# Cursor 编排自检清单

改编自 harness-engineer `PLATFORM_REQUIREMENTS.md`，**非阻塞** — 未通过时降级为单会话顺序执行，不 HALT。

## 快速检查

| # | 检查项 | 通过标准 |
| --- | --- | --- |
| 1 | Subagent 定义 | `.agents/agents/coder.md` 等**七套**角色（含 coder、test-engineer、web-investigator） |
| 2 | 规则加载 | `.cursor/rules/ai-entry.mdc`、`.cursor/rules/cursor-subagent-routing.mdc` 存在 |
| 3 | Skill 可用 | `.agents/skills/cursor-orchestration/SKILL.md` 存在；偏好文档 `orchestration/skill-preferences.zh.md` 可读 |
| 4 | 产物目录 | `.ai-runtime-artifacts/execution-logs/` 存在 |
| 5 | Git 安全 | 在 feature 分支工作；main 受保护 |
| 6 | 验证命令 | `harness-kit/project.verification.md` 可读 |

## 建议但非必须

- MCP 工具已配置且 descriptor 可读
- `.cursor/hooks.json` 已配置
- 并行度已与 `config.defaults.yaml` 对齐

## 降级策略

任一项未通过时：

1. `max_parallel_agents: 1`
2. 不并行委派 subagent，主 Agent 顺序执行（仍遵守阶段门禁）
3. 在 execution-log 中记录 `degraded: true` 及原因
