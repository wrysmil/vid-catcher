# 阻断原生 Plan 模式

本 hook 用于阻断 Claude Code 原生 `EnterPlanMode` / `ExitPlanMode` 工具，确保所有计划产物落入 `.ai-runtime-artifacts/plans/`。

## 正确方式

使用 Harness stage skill 流程：

1. `Load superpowers:writing-plans skill`
2. 按 `artifact-templates/plan.harness-overlay.md` 格式写入
3. 产物路径：`.ai-runtime-artifacts/plans/YYYY-MM-DD-<topic>-plan.md`

## 启用方式

1. 复制本目录下的 `settings.json.example` → `settings.json`
2. 确保 `block-native-plan-mode.sh` 具有可执行权限
