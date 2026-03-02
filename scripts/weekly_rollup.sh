#!/usr/bin/env bash
set -euo pipefail

DAYS="${DAYS:-7}"
BASE_DIR="${BASE_DIR:-$HOME/.openclaw}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STACK_DIR="${STACK_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
LOG_LIMIT_CHARS="${LOG_LIMIT_CHARS:-7000}"

summarize_with_openclaw() {
  local agent_id="$1"
  local logs="$2"
  local prompt
  prompt=$'Extract exactly 3 durable, actionable facts from these logs.\nFormat exactly as:\n- Fact 1\n- Fact 2\n- Fact 3\n\nLogs:\n'
  prompt+="$logs"

  local json
  if ! json=$(openclaw agent --agent "$agent_id" --message "$prompt" --json 2>/dev/null); then
    echo "- Weekly summary unavailable (openclaw agent command failed)."
    return 0
  fi

  python3 - <<'PY' "$json"
import json,sys
try:
    obj=json.loads(sys.argv[1])
    payloads=((obj.get('result') or {}).get('payloads') or [])
    text=''
    if payloads:
        text=payloads[0].get('text','')
    print(text.strip() or '- Weekly summary unavailable (empty response).')
except Exception:
    print('- Weekly summary unavailable (parse error).')
PY
}

for AGENT in main coding; do
  WS="$BASE_DIR/workspace"
  if [[ "$AGENT" == "coding" ]]; then
    WS="$BASE_DIR/workspace-coding"
  fi

  MEM_DIR="$WS/memory"
  MEM_FILE="$WS/MEMORY.md"
  mkdir -p "$MEM_DIR"
  [[ -f "$MEM_FILE" ]] || echo "# MEMORY.md" > "$MEM_FILE"

  LOGS=""
  if compgen -G "$MEM_DIR/*.md" > /dev/null; then
    LOGS=$(find "$MEM_DIR" -type f -name "*.md" -mtime -"$DAYS" -print0 | xargs -0 cat 2>/dev/null | tail -c "$LOG_LIMIT_CHARS" || true)
  fi

  if [[ -z "${LOGS:-}" ]]; then
    SUMMARY='- No recent logs to summarize this week.'
  else
    SUMMARY=$(summarize_with_openclaw "$AGENT" "$LOGS")
  fi

  {
    echo "## $(date -u +%F) Weekly"
    echo "$SUMMARY"
    echo
  } >> "$MEM_FILE"

done

if [[ -x "$STACK_DIR/scripts/sync_all.sh" ]]; then
  "$STACK_DIR/scripts/sync_all.sh" || true
fi

echo "weekly rollup complete"
