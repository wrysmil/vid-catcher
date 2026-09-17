#!/usr/bin/env bash
set -euo pipefail

err() { echo "ERROR: $*" >&2; exit 2; }

usage() {
  cat <<'EOF'
Usage:
  harness-worktree.sh create --repo <path> --date <YYYY-MM-DD> --topic <slug> --wu <WU-01> --wu-type <type> --agent-role <role> --base-ref <ref>
  harness-worktree.sh remove --repo <path> --worktree <path>
  harness-worktree.sh list --repo <path>
EOF
}

cmd="${1:-}"
shift || true

repo=""
date=""
topic=""
wu=""
wu_type=""
agent_role=""
base_ref=""
worktree=""

require() {
  local name="$1"
  local value="$2"
  [[ -n "$value" ]] || err "missing --$name"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) repo="${2:-}"; shift 2 ;;
    --date) date="${2:-}"; shift 2 ;;
    --topic) topic="${2:-}"; shift 2 ;;
    --wu) wu="${2:-}"; shift 2 ;;
    --wu-type) wu_type="${2:-}"; shift 2 ;;
    --agent-role) agent_role="${2:-}"; shift 2 ;;
    --base-ref) base_ref="${2:-}"; shift 2 ;;
    --worktree) worktree="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) err "unknown arg: $1" ;;
  esac
done

[[ -n "$cmd" ]] || { usage; exit 2; }

git_ok() {
  git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1
}

ensure_ignored() {
  # check-ignore is more reliable when the path exists
  mkdir -p "$repo/.worktrees"
  local probe="$repo/.worktrees/.harness-ignore-probe"
  : > "$probe"
  git -C "$repo" check-ignore -q ".worktrees/.harness-ignore-probe" >/dev/null 2>&1 || err ".worktrees/ is not ignored; add to .gitignore first"
}

case "$cmd" in
  create)
    require "repo" "$repo"
    require "date" "$date"
    require "topic" "$topic"
    require "wu" "$wu"
    require "wu-type" "$wu_type"
    require "agent-role" "$agent_role"
    require "base-ref" "$base_ref"
    git_ok || err "not a git repo: $repo"
    ensure_ignored

    wt_rel=".worktrees/${date}--${topic}__${wu}__${wu_type}__${agent_role}"
    wt_path="${repo}/${wt_rel}"
    branch="wu/${date}/${topic}/${wu}-${wu_type}"

    if [[ -e "$wt_path" ]]; then
      err "worktree already exists: $wt_path"
    fi

    git -C "$repo" worktree add "$wt_path" -b "$branch" "$base_ref" >/dev/null

    cat <<EOF
worktree_path=$wt_rel
branch=$branch
EOF
    ;;

  remove)
    require "repo" "$repo"
    require "worktree" "$worktree"
    git_ok || err "not a git repo: $repo"
    git -C "$repo" worktree remove -f "$worktree" >/dev/null
    ;;

  list)
    require "repo" "$repo"
    git_ok || err "not a git repo: $repo"
    if [[ -d "$repo/.worktrees" ]]; then
      (cd "$repo" && ls -1 ".worktrees") || true
    fi
    ;;

  *)
    usage
    exit 2
    ;;
esac

