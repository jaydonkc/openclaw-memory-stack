#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

[[ -f .env ]] || { echo "Missing .env (copy from .env.example first)"; exit 1; }

set -a
source .env
set +a

ROLLUP_ENABLE_DAILY="${ROLLUP_ENABLE_DAILY:-1}"
ROLLUP_ENABLE_WEEKLY="${ROLLUP_ENABLE_WEEKLY:-1}"
ROLLUP_DAILY_CRON="${ROLLUP_DAILY_CRON:-0 2 * * *}"
ROLLUP_WEEKLY_CRON="${ROLLUP_WEEKLY_CRON:-0 3 * * 0}"

DAILY_CMD="$ROOT_DIR/scripts/daily_rollup.sh >> /tmp/openclaw_daily_rollup.log 2>&1"
WEEKLY_CMD="$ROOT_DIR/scripts/weekly_rollup.sh >> /tmp/openclaw_weekly_rollup.log 2>&1"

existing="$(crontab -l 2>/dev/null || true)"
filtered="$(printf "%s\n" "$existing" | grep -v 'daily_rollup.sh' | grep -v 'weekly_rollup.sh' || true)"

new="$filtered"
if [[ "$ROLLUP_ENABLE_DAILY" == "1" ]]; then
  new+=$'\n'"$ROLLUP_DAILY_CRON $DAILY_CMD"
fi
if [[ "$ROLLUP_ENABLE_WEEKLY" == "1" ]]; then
  new+=$'\n'"$ROLLUP_WEEKLY_CRON $WEEKLY_CMD"
fi

printf "%s\n" "$new" | sed '/^$/d' | crontab -

echo "Installed rollup cron entries:" 
crontab -l | grep -E 'daily_rollup|weekly_rollup' || echo "(none)"
