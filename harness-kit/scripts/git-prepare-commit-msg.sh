#!/usr/bin/env bash
set -euo pipefail
MSG_FILE="${1:?}"
[[ -f "$MSG_FILE" ]] || exit 0
if [[ "$(uname -s)" == "Darwin" ]]; then
  sed -i '' -E '/^[[:space:]]*(Co-authored-by|Made-with):[[:space:]]*Cursor/d' "$MSG_FILE"
  sed -i '' -E '/cursoragent@cursor\.com/d' "$MSG_FILE"
else
  sed -i -E '/^[[:space:]]*(Co-authored-by|Made-with):[[:space:]]*Cursor/d' "$MSG_FILE"
  sed -i -E '/cursoragent@cursor\.com/d' "$MSG_FILE"
fi
