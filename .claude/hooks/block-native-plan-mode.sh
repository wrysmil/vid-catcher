#!/usr/bin/env bash
# block-native-plan-mode.sh
# 阻断 Claude Code 原生 EnterPlanMode / ExitPlanMode 工具
# 使用前需将此文件设为可执行：chmod +x block-native-plan-mode.sh
# 并将 settings.json.example 复制为 settings.json

echo "Harness: 原生 plan 工具已阻断，请使用 Harness stage skill 流程"
echo "正确方式: Load superpowers:writing-plans skill → Write .ai-runtime-artifacts/plans/YYYY-MM-DD-<topic>-plan.md"
exit 1
