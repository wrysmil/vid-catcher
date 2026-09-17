#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 检测布局：source = 本仓库（core/ 在根）；deployed = 已接入目标项目（harness-kit/ 子目录）
if [[ -f "$KIT_ROOT/core/harness.md" ]]; then
  LAYOUT="source"
  ROOT_DIR="$KIT_ROOT"
  HK="."
elif [[ -f "$KIT_ROOT/harness-kit/core/harness.md" ]]; then
  LAYOUT="deployed"
  ROOT_DIR="$KIT_ROOT"
  HK="harness-kit"
else
  echo "cannot detect harness-kit layout under $KIT_ROOT" >&2
  exit 1
fi

cd "$ROOT_DIR"
echo "==> layout: $LAYOUT (root: $ROOT_DIR)"

kit_path() {
  if [[ "$HK" == "." ]]; then
    echo "$1"
  else
    echo "$HK/$1"
  fi
}

required_kit_files=(
  "README.md"
  "core/harness.md"
  "project.profile.md"
  "context-map.md"
  "project.verification.md"
  "project.git.md"
  "core/routing.md"
  "core/capabilities/registry.md"
  "core/capabilities/primitives.md"
  "core/orchestration/dispatcher-workflow.md"
  "core/orchestration/skill-preferences.md"
  "core/orchestration/config.defaults.yaml"
  "core/orchestration/tracking/schema.md"
  "core/artifacts.md"
  "init/bootstrap.prompt.md"
  "init/onboarding-handoff.txt"
  "init/project-profiler.prompt.md"
  "init/templates/project.profile.md"
  "init/templates/branch.profile.md"
  "init/templates/context-map.md"
  "init/templates/project.verification.md"
  "init/templates/project.git.md"
  "artifact-templates/spec.md"
  "artifact-templates/plan.md"
  "artifact-templates/spec.harness-overlay.md"
  "artifact-templates/plan.harness-overlay.md"
  "artifact-templates/dispatch.harness-overlay.md"
  "artifact-templates/verification.md"
  "artifact-templates/verification-lite.md"
  "artifact-templates/collective-test.md"
  "artifact-templates/code-review.md"
  "artifact-templates/document-review.md"
  "artifact-templates/decision.md"
  "artifact-templates/dispatch-track.md"
  "artifact-templates/handoff.md"
  "artifact-templates/progress.md"
  "artifact-templates/wu-checklist.md"
  "artifact-templates/research-report.md"
  "core/orchestration/claude-continuous-loop.md"
  "platform/cursor/.cursor/rules/ai-entry.mdc"
  "platform/cursor/.cursor/rules/cursor-subagent-routing.mdc"
  ".agents/skills/test-driven-development/SKILL.md"
  ".agents/skills/verification-before-completion/SKILL.md"
  ".agents/skills/ui-ux-pro-max/SKILL.md"
  ".agents/skills/ui-ux-pro-max/scripts/search.py"
  "scripts/install-ai-skills.sh"
  "scripts/harness-check.sh"
)

# 共享层 deployed 文件（所有平台都需要）
required_deployed_shared=(
  "AGENTS.md"
  "CLAUDE.md"
  ".agents/README.md"
  ".agents/agents/coder.md"
  ".agents/agents/implementer.md"
  ".agents/agents/reviewer.md"
  ".agents/agents/explorer.md"
  ".agents/agents/debugger.md"
  ".agents/agents/test-engineer.md"
  ".agents/agents/smoke-tester.md"
  ".agents/agents/web-investigator.md"
  ".agents/skills/orchestration/SKILL.md"
  ".agents/skills/orchestration/SKILL.md"
  ".agents/skills/test-driven-development/SKILL.md"
  ".agents/skills/verification-before-completion/SKILL.md"
  ".ai-runtime-artifacts/README.md"
  ".mcp.json"
)

# Cursor 平台层 deployed 文件
required_deployed_cursor=(
  ".cursor/rules/ai-entry.mdc"
  ".cursor/rules/cursor-subagent-routing.mdc"
)

required_dirs=(
  ".ai-runtime-artifacts/specs"
  ".ai-runtime-artifacts/plans"
  ".ai-runtime-artifacts/reviews"
  ".ai-runtime-artifacts/verifications"
  ".ai-runtime-artifacts/decisions"
  ".ai-runtime-artifacts/retros"
  ".ai-runtime-artifacts/research"
  ".ai-runtime-artifacts/execution-logs"
  ".ai-runtime-artifacts/execution-logs/tracking"
)

missing=0
for rel in "${required_kit_files[@]}"; do
  file="$(kit_path "$rel")"
  if [[ -f "$file" ]]; then
    echo "ok: $file"
  else
    echo "missing: $file" >&2
    missing=1
  fi
done

if [[ "$LAYOUT" == "deployed" ]]; then
  # 共享层文件
  for file in "${required_deployed_shared[@]}"; do
    if [[ -f "$file" ]]; then
      echo "ok: $file"
    else
      echo "missing: $file" >&2
      missing=1
    fi
  done

  # Cursor 平台层文件（按需检查）
  if [[ -d ".cursor" ]]; then
    for file in "${required_deployed_cursor[@]}"; do
      if [[ -f "$file" ]]; then
        echo "ok: $file"
      else
        echo "missing: $file" >&2
        missing=1
      fi
    done
  fi


  # 目录
  for dir in "${required_dirs[@]}"; do
    if [[ -d "$dir" ]]; then
      echo "ok: $dir"
    else
      echo "missing: $dir" >&2
      missing=1
    fi
  done
else
  echo "skip: deployed-only projection checks (source layout)"
fi

if [[ "$missing" -ne 0 ]]; then
  exit 1
fi

# Claude 平台层（源在 kit 根 .claude/；deployed 时投影到项目根 .claude/）
# 必查 leader.md（会话自动注入）+ hooks 模板（block-native-plan-mode 是真门禁，opt-in 启用由 settings.json 决定）
echo "==> Checking Claude platform layer (.claude/)"
claude_errors=0
if [[ "$LAYOUT" == "source" ]]; then
  claude_root="$KIT_ROOT"
elif [[ -d ".claude" ]]; then
  claude_root="$ROOT_DIR"
else
  claude_root=""
  echo "skip: .claude/ (not projected; Cursor-only?)"
fi
if [[ -n "$claude_root" ]]; then
  if [[ -f "$claude_root/.claude/rules/leader.md" ]]; then
    echo "ok: .claude/rules/leader.md"
  else
    echo "missing: .claude/rules/leader.md (Leader 行为规范；Claude 会话自动注入)" >&2
    claude_errors=1
  fi
  for file in ".claude/hooks/block-native-plan-mode.sh" ".claude/settings.json.example"; do
    if [[ -f "$claude_root/$file" ]]; then
      echo "ok: $file"
    else
      echo "missing: $file (opt-in hook 模板，缺失即无法启用原生 plan 阻断)" >&2
      claude_errors=1
    fi
  done
fi

if [[ "$claude_errors" -ne 0 ]]; then
  exit 1
fi

echo "==> Checking harness subagent manifests (.agents/agents/)"
agent_errors=0
agents_dir="$(kit_path .agents/agents)"
max_projection_lines=400

if [[ -d "$agents_dir" ]]; then
  for projected in "$agents_dir"/*.md; do
    [[ -f "$projected" ]] || continue
    rel_projected="${projected#"$ROOT_DIR"/}"
    rel_projected="${rel_projected#./}"
    lines="$(wc -l < "$projected" | tr -d ' ')"
    if [[ "$lines" -gt "$max_projection_lines" ]]; then
      echo "manifest exceeds ${max_projection_lines} lines ($lines): $rel_projected" >&2
      agent_errors=1
    fi
    if ! head -1 "$projected" | grep -q '^---$' 2>/dev/null; then
      echo "manifest missing YAML frontmatter: $rel_projected" >&2
      agent_errors=1
    fi
  done
else
  if [[ "$LAYOUT" == "source" ]]; then
    echo "skip: .agents/agents/ not present (source layout)" >&2
  else
    echo "missing: .agents/agents/" >&2
    agent_errors=1
  fi
fi

if [[ "$agent_errors" -ne 0 ]]; then
  exit 1
fi

echo "==> Checking orchestration stub redirects (skipped — stubs deleted after shared layer migration)"

echo "==> Checking capability matrix coverage"
matrix_errors=0
registry="$(kit_path core/capabilities/registry.md)"
if [[ ! -f "$registry" ]]; then
  echo "missing registry: $registry" >&2
  matrix_errors=1
else
  capability_ids=()
  while IFS= read -r cap_line; do
    [[ -n "$cap_line" ]] && capability_ids+=("$cap_line")
  done < <(grep -E '^### [a-z0-9.-]+$' "$registry" | sed 's/^### //')
  for platform in cursor claude trae; do
    matrix="$(kit_path "platform/$platform/capability-matrix.yaml")"
    bindings="$(kit_path "platform/$platform/bindings.md")"
    if [[ ! -f "$matrix" ]]; then
      echo "missing matrix: $matrix" >&2
      matrix_errors=1
      continue
    fi
    if [[ ! -f "$bindings" ]]; then
      echo "missing bindings: $bindings" >&2
      matrix_errors=1
    fi
    for cap_id in "${capability_ids[@]}"; do
      if ! grep -q "^  ${cap_id}:" "$matrix" 2>/dev/null; then
        echo "matrix missing capability $cap_id: $matrix" >&2
        matrix_errors=1
      fi
    done
    while IFS= read -r cap_key; do
      [[ -n "$cap_key" ]] || continue
      block="$(awk -v key="$cap_key" '
        $0 ~ "^  " key ":" { show=1; print; next }
        show && /^  [a-z]/ { exit }
        show { print }
      ' "$matrix")"
      if printf '%s\n' "$block" | grep -q 'status: degraded'; then
        if [[ -f "$bindings" ]] && ! grep -qE "${cap_key}|degraded" "$bindings" 2>/dev/null; then
          echo "degraded capability $cap_key lacks bindings note: $bindings" >&2
          matrix_errors=1
        fi
      fi
    done < <(grep -E '^  [a-z][a-z0-9.-]*:' "$matrix" 2>/dev/null | sed -n 's/^  \([a-z0-9.-]*\):.*/\1/p')
    echo "ok: matrix $platform (${#capability_ids[@]} capabilities)"
  done
fi

routing_file="$(kit_path core/routing.md)"
if [[ -f "$routing_file" ]]; then
  if ! grep -q 'orchestration' "$routing_file" 2>/dev/null; then
    echo "routing missing orchestration column/reference" >&2
    matrix_errors=1
  else
    echo "ok: routing orchestration"
  fi
fi

if [[ "$matrix_errors" -ne 0 ]]; then
  exit 1
fi

echo "==> Checking unfinished markers"
scan_paths=()
if [[ "$LAYOUT" == "deployed" ]]; then
  scan_paths=(AGENTS.md CLAUDE.md .cursor .agents)
fi
scan_paths+=("$(kit_path .)")
if [[ -d ".ai-runtime-artifacts" ]]; then
  scan_paths+=(".ai-runtime-artifacts")
fi

if grep -nE "T[B]D|T[O]DO|FIX[M]E|待[定]|占[位]" "${scan_paths[@]}" 2>/dev/null; then
  echo "unfinished markers found" >&2
  exit 1
fi

if [[ -d ".ai-runtime-artifacts" ]]; then
  echo "==> Checking AI runtime artifact front matter"
  artifact_errors=0
  while IFS= read -r artifact_file; do
    if [[ "$(sed -n '1p' "$artifact_file")" != "---" ]]; then
      echo "missing front matter: $artifact_file" >&2
      artifact_errors=1
      continue
    fi

    front_matter="$(awk '
      NR == 1 && $0 == "---" { in_fm = 1; next }
      in_fm && $0 == "---" { exit }
      in_fm { print }
    ' "$artifact_file")"
    for key in artifact route skills source created_at; do
      if ! printf '%s\n' "$front_matter" | grep -qE "^${key}:"; then
        echo "missing front matter key '$key': $artifact_file" >&2
        artifact_errors=1
      fi
    done

    if printf '%s\n' "$front_matter" | grep -qiE '^route:.*(brainstorming|writing-plans|verification-before-completion|git-xywh|orchestration)'; then
      skill_items="$(printf '%s\n' "$front_matter" | awk '
        /^skills:/ { f = 1; next }
        f && /^[A-Za-z0-9_.-]+:/ { exit }
        f && /^[[:space:]]*-[[:space:]]+/ { sub(/^[[:space:]]*-[[:space:]]+/, ""); print }
      ')"
      if [[ -z "$skill_items" ]] || printf '%s\n' "$skill_items" | grep -qxE '<skill>'; then
        echo "empty or placeholder skills (route requires stage skill): $artifact_file" >&2
        artifact_errors=1
      fi
      evidence_items="$(printf '%s\n' "$front_matter" | awk '
        /^skills_evidence:/ { f = 1; next }
        f && /^[A-Za-z0-9_.-]+:/ { exit }
        f && /^[[:space:]]*-[[:space:]]+/ { sub(/^[[:space:]]*-[[:space:]]+/, ""); print }
      ')"
      if [[ -z "$evidence_items" ]] || printf '%s\n' "$evidence_items" | grep -qE '^(<path|<skill>|\.{3})'; then
        echo "missing or placeholder skills_evidence (P1 required for stage-skill route): $artifact_file" >&2
        artifact_errors=1
      fi
    fi
  done < <(find .ai-runtime-artifacts -type f -name '*.md' ! -name 'README.md' 2>/dev/null | sort)

  if [[ "$artifact_errors" -ne 0 ]]; then
    exit 1
  fi
else
  echo "skip: .ai-runtime-artifacts (not initialized)"
fi

# spec §10 门禁：execution-log 声称批次完成但无 collective-test / code-review
# 引用时升级为 ERROR（gap #6 治本）；含编排上下文但缺尾盘链接仍为 WARN
#
# 路径位置（gap #1、#2 治本 + Q4.2 风险）：
# - consumer 项目：closeout 产物在 .ai-runtime-artifacts/execution-logs/*.md
# - harness-kit 仓库自身：closeout 示例在 docs/runtime/closeouts/*-execution-log.md
#   （.ai-runtime-artifacts/ 被 .gitignore 排除）
# 因此 closeout 段扫**两个**位置。
#
# 自残保护（gap #11 治本）：
# harness-kit 仓库（marker = core/harness.md）—— ERROR 改 WARN，避免本仓
# closeout 示例**自残**（harness-check 在本仓库跑会扫到示例文件）。
is_harness_kit_self=0
if [[ -f "core/harness.md" ]]; then
  is_harness_kit_self=1
fi

closeout_error=0
if [[ -d ".ai-runtime-artifacts/execution-logs" || -d "docs/runtime/closeouts" ]]; then
  if [[ "$is_harness_kit_self" -eq 1 ]]; then
    echo "==> Checking execution-log batch-closeout (WARN only — harness-kit self, 避免自残)"
  else
    echo "==> Checking execution-log batch-closeout (WARN + spec §10 ERROR)"
  fi
  closeout_warn=0
  # 扫两位置：consumer 侧（.ai-runtime-artifacts/execution-logs/）+ harness-kit 仓库示例（docs/runtime/closeouts/）
  while IFS= read -r elog; do
    [[ -f "$elog" ]] || continue
    base="$(basename "$elog")"
    [[ "$base" == "HANDOFF.md" ]] && continue
    [[ "$base" == README.md ]] && continue
    # harness-kit 仓库示例文件命名：*-execution-log.md；其他（collective-test / code-review）跳过
    case "$elog" in
      docs/runtime/closeouts/*-execution-log.md) ;;
      .ai-runtime-artifacts/execution-logs/*.md) ;;
      *) continue ;;
    esac
    content="$(<"$elog")"
    if ! printf '%s' "$content" | grep -qE 'orchestration|dispatcher-workflow'; then
      continue
    fi
    missing=()
    if ! printf '%s' "$content" | grep -qE '尾盘门禁|collective-test'; then
      missing+=("尾盘门禁或 collective-test 链接")
    fi
    if ! printf '%s' "$content" | grep -qE 'code-review'; then
      missing+=("code-review 链接")
    fi
    if [[ ${#missing[@]} -gt 0 ]]; then
      echo "warn: $elog — Cursor 编排 execution-log 建议含尾盘产物引用（${missing[*]}）。见 docs/superpowers/specs/2026-05-28-batch-closeout-review-and-collective-test.md" >&2
      closeout_warn=1
    fi
    if printf '%s' "$content" | grep -qiE '批次交付完成|本 GROUP.*完成|GROUP 交付完成'; then
      if ! printf '%s' "$content" | grep -qE 'collective-test.*PASS|verdict: PASS'; then
        if [[ "$is_harness_kit_self" -eq 1 ]]; then
          echo "warn: $elog — harness-kit self — 声称批次完成但未引用 collective-test PASS（不阻断）" >&2
          closeout_warn=1
        else
          echo "ERROR: $elog — 声称批次完成但未引用 collective-test PASS（spec §10 门禁）。见 docs/superpowers/specs/2026-05-28-batch-closeout-review-and-collective-test.md" >&2
          closeout_error=1
        fi
      fi
      if ! printf '%s' "$content" | grep -qE 'code-review|verdict: APPROVE|verdict: SKIPPED'; then
        if [[ "$is_harness_kit_self" -eq 1 ]]; then
          echo "warn: $elog — harness-kit self — 声称批次完成但未引用 code-review APPROVE/SKIPPED（不阻断）" >&2
          closeout_warn=1
        else
          echo "ERROR: $elog — 声称批次完成但未引用 code-review APPROVE/SKIPPED（spec §10 门禁）。见 docs/superpowers/specs/2026-05-28-batch-closeout-review-and-collective-test.md" >&2
          closeout_error=1
        fi
      fi
    fi
  done < <(find .ai-runtime-artifacts/execution-logs -maxdepth 1 -type f -name '*.md' 2>/dev/null; find docs/runtime/closeouts -maxdepth 1 -type f -name '*-execution-log.md' 2>/dev/null | sort)
  if [[ "$closeout_warn" -eq 0 ]] && [[ "$closeout_error" -eq 0 ]]; then
    echo "ok: execution-log batch-closeout (no warnings)"
  fi
fi
if [[ "$closeout_error" -ne 0 ]]; then
  exit 1
fi

# 路径合规检查：扫描 docs/superpowers/ 是否有本应属于 .ai-runtime-artifacts/ 的产物文件
# 目的：检测 AI 是否把产物写错位置（spec/plan/verification/review 等）
echo "==> Checking artifact path compliance (docs/ vs .ai-runtime-artifacts/)"
artifact_path_warn=0

# 定义本应属于 .ai-runtime-artifacts/ 的产物文件命名模式（使用 bash glob 避免 grep 依赖）
# spec: YYYY-MM-DD-*-spec.md 或 YYYY-MM-DD-*-spec-*.md
# plan: YYYY-MM-DD-*-plan.md 或 YYYY-MM-DD-*-plan-*.md
# verification: YYYY-MM-DD-*-verification*.md
# collective-test: YYYY-MM-DD-*-collective-test.md
# code-review: YYYY-MM-DD-*-code-review.md
# document-review: YYYY-MM-DD-*-document-review.md

# 扫描 docs/superpowers/specs/
if [[ -d "docs/superpowers/specs" ]]; then
  for f in docs/superpowers/specs/*.md; do
    [[ -f "$f" ]] || continue
    base="$(basename "$f")"
    [[ "$base" == README.md ]] && continue
    # 匹配 spec 命名模式
    if [[ "$base" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}-.+-spec.*\.md$ ]]; then
      echo "warn: spec artifact found in docs/superpowers/specs/ instead of .ai-runtime-artifacts/specs/: $f" >&2
      echo "      移动到: .ai-runtime-artifacts/specs/$base" >&2
      artifact_path_warn=1
    fi
  done
fi

# 扫描 docs/superpowers/plans/
if [[ -d "docs/superpowers/plans" ]]; then
  for f in docs/superpowers/plans/*.md; do
    [[ -f "$f" ]] || continue
    base="$(basename "$f")"
    [[ "$base" == README.md ]] && continue
    # 匹配 plan 命名模式
    if [[ "$base" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}-.+-plan.*\.md$ ]]; then
      echo "warn: plan artifact found in docs/superpowers/plans/ instead of .ai-runtime-artifacts/plans/: $f" >&2
      echo "      移动到: .ai-runtime-artifacts/plans/$base" >&2
      artifact_path_warn=1
    fi
  done
fi

# 扫描 docs/superpowers/verifications/
if [[ -d "docs/superpowers/verifications" ]]; then
  for f in docs/superpowers/verifications/*.md; do
    [[ -f "$f" ]] || continue
    base="$(basename "$f")"
    [[ "$base" == README.md ]] && continue
    # 匹配 verification / collective-test 命名模式
    if [[ "$base" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}-.+-verification.*\.md$ ]] || \
       [[ "$base" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}-.+-collective-test\.md$ ]]; then
      echo "warn: verification artifact found in docs/superpowers/verifications/ instead of .ai-runtime-artifacts/verifications/: $f" >&2
      echo "      移动到: .ai-runtime-artifacts/verifications/$base" >&2
      artifact_path_warn=1
    fi
  done
fi

# 扫描 docs/superpowers/reviews/
if [[ -d "docs/superpowers/reviews" ]]; then
  for f in docs/superpowers/reviews/*.md; do
    [[ -f "$f" ]] || continue
    base="$(basename "$f")"
    [[ "$base" == README.md ]] && continue
    # 匹配 review / code-review / document-review 命名模式
    if [[ "$base" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}-.+-review.*\.md$ ]]; then
      echo "warn: review artifact found in docs/superpowers/reviews/ instead of .ai-runtime-artifacts/reviews/: $f" >&2
      echo "      移动到: .ai-runtime-artifacts/reviews/$base" >&2
      artifact_path_warn=1
    fi
  done
fi

# 扫描 docs/superpowers/decisions/
if [[ -d "docs/superpowers/decisions" ]]; then
  for f in docs/superpowers/decisions/*.md; do
    [[ -f "$f" ]] || continue
    base="$(basename "$f")"
    [[ "$base" == README.md ]] && continue
    # 匹配 decision 命名模式
    if [[ "$base" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}-.+-decision.*\.md$ ]]; then
      echo "warn: decision artifact found in docs/superpowers/decisions/ instead of .ai-runtime-artifacts/decisions/: $f" >&2
      echo "      移动到: .ai-runtime-artifacts/decisions/$base" >&2
      artifact_path_warn=1
    fi
  done
fi

# 扫描 docs/superpowers/retros/
if [[ -d "docs/superpowers/retros" ]]; then
  for f in docs/superpowers/retros/*.md; do
    [[ -f "$f" ]] || continue
    base="$(basename "$f")"
    [[ "$base" == README.md ]] && continue
    # 匹配 retro 命名模式
    if [[ "$base" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}-.+-retro.*\.md$ ]]; then
      echo "warn: retro artifact found in docs/superpowers/retros/ instead of .ai-runtime-artifacts/retros/: $f" >&2
      echo "      移动到: .ai-runtime-artifacts/retros/$base" >&2
      artifact_path_warn=1
    fi
  done
fi

if [[ "$artifact_path_warn" -eq 0 ]]; then
  echo "ok: artifact path compliance"
fi

# 检查 artifact-templates/*.md 的 front matter 路径是否真实存在
# 目的：挡 gap #3、#4、#5 —— 模板自身 FM 写错路径此前无人发现
echo "==> Checking artifact-templates FM paths"
tmpl_errors=0
tmpl_warn=0
for tmpl in artifact-templates/*.md; do
  [[ -f "$tmpl" ]] || continue
  base="$(basename "$tmpl")"
  [[ "$base" == "README.md" ]] && continue

  front_matter="$(awk '
    NR == 1 && $0 == "---" { in_fm = 1; next }
    in_fm && $0 == "---" { exit }
    in_fm { print }
  ' "$tmpl")"

  while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    # 启发式：跳过明显非仓库内路径（纯 bash glob，不依赖 rg）
    case "$path" in
      /*|~*) continue ;;                # 绝对路径 / 用户全局
      *\<*|*\>*) continue ;;            # 含占位符
      *' '*|*'（'*|*'）'*|*'，'*) continue ;;  # 含空格 / 全角标点
      *[!A-Za-z0-9._/-]*) continue ;;   # 含其他非路径字符（含中文自由文本）
      */*/.*|*.md|*/*/*.md) ;;           # 像仓库内 .md 路径
      *) continue ;;                     # 不像路径的占位符（如 user-query）
    esac
    if [[ ! -e "$path" ]]; then
      echo "warn: missing skills_evidence path: $path (in $tmpl)" >&2
      tmpl_warn=1
    fi
  done < <(printf '%s\n' "$front_matter" | awk '
    /^skills_evidence:/ { f = 1; next }
    f && /^[A-Za-z0-9_.-]+:/ { exit }
    f && /^[[:space:]]*-[[:space:]]+/ { sub(/^[[:space:]]*-[[:space:]]+/, ""); print }
  ')

  while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    case "$path" in
      /*|~*) continue ;;
      *\<*|*\>*) continue ;;
      *' '*|*'（'*|*'）'*|*'，'*) continue ;;
      *[!A-Za-z0-9._/-]*) continue ;;
      */*/.*|*.md|*/*/*.md) ;;
      *) continue ;;
    esac
    if [[ ! -e "$path" ]]; then
      echo "warn: missing source path: $path (in $tmpl)" >&2
      tmpl_warn=1
    fi
  done < <(printf '%s\n' "$front_matter" | awk '
    /^source:/ { f = 1; next }
    f && /^[A-Za-z0-9_.-]+:/ { exit }
    f && /^[[:space:]]*-[[:space:]]+/ { sub(/^[[:space:]]*-[[:space:]]+/, ""); print }
  ')
done
if [[ "$tmpl_warn" -eq 0 ]]; then
  echo "ok: artifact-templates FM paths"
fi

if [[ -f package.json ]]; then
  echo "==> Checking package.json"
  node -e "JSON.parse(require('fs').readFileSync('package.json','utf8')); console.log('package-json-ok')"
else
  echo "skip: package.json (not present)"
fi

echo "==> Checking shell scripts"
bash -n "$(kit_path scripts/install-ai-skills.sh)"
bash -n "$(kit_path scripts/harness-check.sh)"
bash -n "$(kit_path scripts/harness-project.sh)"

echo "==> Harness check complete"
