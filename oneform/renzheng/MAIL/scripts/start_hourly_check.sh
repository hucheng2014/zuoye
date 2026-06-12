#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNS_DIR="$ROOT/MAIL/runs"
mkdir -p "$RUNS_DIR"

PID_FILE="$RUNS_DIR/hourly-check.pid"
LOG_FILE="$RUNS_DIR/hourly-check.log"

if [[ -f "$PID_FILE" ]]; then
  OLD_PID="$(cat "$PID_FILE" || true)"
  if [[ -n "$OLD_PID" ]] && kill -0 "$OLD_PID" 2>/dev/null; then
    echo "MAIL hourly checker already running: PID $OLD_PID"
    exit 0
  fi
fi

cd "$ROOT"
nohup node MAIL/scripts/hourly_check.js >> "$LOG_FILE" 2>&1 &
PID="$!"
echo "$PID" > "$PID_FILE"
echo "Started MAIL hourly checker: PID $PID"
echo "Log: $LOG_FILE"
