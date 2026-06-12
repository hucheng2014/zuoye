#!/bin/bash
# Keep AD auto daemon running (per-task LLM judgment, no hardcoded ratings).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
DAEMON="$ROOT/auto_ad_daemon.py"
LOG="$ROOT/runs/auto_ad_watchdog.log"
PIDFILE="$ROOT/runs/auto_ad_daemon.pid"
mkdir -p "$ROOT/runs"

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

# Load API env if present (no secret output)
[ -f "$HOME/.bashrc" ] && source "$HOME/.bashrc" >/dev/null 2>&1 || true

while true; do
  if ! pgrep -f "auto_ad_daemon.py" >/dev/null 2>&1; then
    log "auto_ad_daemon not running — starting"
    setsid env AD_SUBMIT_WAIT_SEC=540 python3 "$DAEMON" >> "$ROOT/runs/auto_ad_daemon.log" 2>&1 &
    echo $! > "$PIDFILE"
    log "started pid=$(cat "$PIDFILE")"
  fi
  sleep 30
done
