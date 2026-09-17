#!/usr/bin/env bash
# 按当前平台选择性安装/检查 AI runtime 与 skill。
# cursor: ~/.cursor/skills/ 检查
# claude: ~/.claude/skills/ 检查
# trae:   ~/.trae/skills/   检查
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PLATFORM=""

SUPERPOWERS_SKILLS=(brainstorming writing-plans systematic-debugging test-driven-development verification-before-completion)
ORG_SKILLS=(git-xywh)

usage() {
  cat <<'EOF'
用法: install-ai-skills.sh [--platform P]

平台: cursor, claude, trae
默认: 自动检测（harness-project.sh detect）

环境变量:
  STRICT_SUPERPOWERS=1   缺 superpowers skill 时退出码 2
  STRICT_ORG_SKILLS=1    缺 org skill（git-xywh）时退出码 2
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform) PLATFORM="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知选项: $1" >&2; usage; exit 1 ;;
  esac
done

# ─── 平台检测 ───────────────────────────────────────────────

if [[ -z "$PLATFORM" ]]; then
  PLATFORM="$(bash "$SCRIPT_DIR/harness-project.sh" detect 2>/dev/null || echo unknown)"
fi

if [[ -z "$PLATFORM" || "$PLATFORM" == "unknown" ]]; then
  echo "无法自动检测平台，请用 --platform 指定: cursor, claude, trae" >&2
  exit 1
fi

echo "==> 目标平台: $PLATFORM"

# ─── 公共: skill 存在性检查 ─────────────────────────────────

check_skill_set() {
  local set_name="$1"
  local search_dir="$2"
  shift 2
  local skills=("$@")
  local missing=0

  for skill in "${skills[@]}"; do
    if [[ -f "$search_dir/$skill/SKILL.md" ]]; then
      echo "ok: $search_dir/$skill/SKILL.md"
    else
      echo "missing: $skill"
      missing=1
    fi
  done

  [[ "$missing" -eq 0 ]] && return 0

  case "$set_name" in
    superpowers)
      cat <<'MSG' >&2

Some superpowers skills are missing. Install via:
  npx skills add obra/superpowers -g
MSG
      if [[ "${STRICT_SUPERPOWERS:-0}" == "1" ]]; then
        exit 2
      fi
      ;;
    org)
      cat <<MSG >&2

Organization skill git-xywh is missing. Install per team docs (slug: git-xywh), e.g. into:
  $search_dir/git-xywh/SKILL.md

Until installed, Git tasks must still read harness-kit/project.git.md and follow repo hooks/CI;
Harness routing expects Leader to invoke git-xywh before commit / branch / MR.
MSG
      if [[ "${STRICT_ORG_SKILLS:-0}" == "1" ]]; then
        exit 2
      fi
      ;;
  esac
}

# ─── 其他平台: 只做 skill 存在性检查 ───────────────────────

check_cursor() {
  echo "==> Checking skills (cursor path: ~/.cursor/skills/)"
  check_skill_set superpowers "$HOME/.cursor/skills" "${SUPERPOWERS_SKILLS[@]}"
  check_skill_set org "$HOME/.cursor/skills" "${ORG_SKILLS[@]}"
}

check_claude() {
  echo "==> Checking skills (claude path: ~/.claude/skills/)"
  check_skill_set superpowers "$HOME/.claude/skills" "${SUPERPOWERS_SKILLS[@]}"
  check_skill_set org "$HOME/.claude/skills" "${ORG_SKILLS[@]}"
}

check_trae() {
  echo "==> Checking skills (trae path: ~/.trae/skills/)"
  check_skill_set superpowers "$HOME/.trae/skills" "${SUPERPOWERS_SKILLS[@]}"
  check_skill_set org "$HOME/.trae/skills" "${ORG_SKILLS[@]}"
}

# ─── 分发 ──────────────────────────────────────────────────

case "$PLATFORM" in
  cursor) check_cursor ;;
  claude) check_claude ;;
  trae)   check_trae ;;
  *)
    echo "未知平台: $PLATFORM" >&2
    exit 1
    ;;
esac

echo "==> AI skills 安装/检查完成（平台: $PLATFORM）"
