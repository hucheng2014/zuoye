#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNS_DIR="$ROOT/MAIL/runs"
mkdir -p "$RUNS_DIR"

PID_FILE="$RUNS_DIR/keepalive.pid"
LOG_FILE="$RUNS_DIR/keepalive.log"

if [[ -f "$PID_FILE" ]]; then
  OLD_PID="$(cat "$PID_FILE" || true)"
  if [[ -n "$OLD_PID" ]] && kill -0 "$OLD_PID" 2>/dev/null; then
    echo "Starshot Keepalive already running: PID $OLD_PID"
    exit 0
  fi
fi

cd "$ROOT"
nohup /Users/xaa/.nvm/versions/node/v24.15.0/bin/node MAIL/scripts/starshot_keepalive.js >> "$LOG_FILE" 2>&1 &
PID="$!"
echo "$PID" > "$PID_FILE"
echo "Started Starshot Keepalive: PID $PID"
echo "Log: $LOG_FILE"
