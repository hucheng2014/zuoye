#!/bin/bash
# Watchdog: keep TAMESSAGE keepalive running until submitted.flag appears, then restart for new task.
set -u
ROOT="/Users/xaa/zuoye/oneform/renzheng"
KEEPALIVE="$ROOT/TAMESSAGE/scripts/keepalive.js"
RUNS="$ROOT/TAMESSAGE/runs"
LOG="$RUNS/watchdog.log"
INTERVAL=15

mkdir -p "$RUNS"
log() { echo "[$(date -Iseconds)] $*" >> "$LOG"; }

start_keepalive() {
  # Only one CDP client allowed — kill extras first
  local pids
  pids=$(pgrep -f "node TAMESSAGE/scripts/keepalive.js" 2>/dev/null || true)
  local count=$(echo "$pids" | grep -c . 2>/dev/null || echo 0)
  if [ "$count" -gt 1 ]; then
    log "Multiple keepalive detected ($count) — keeping oldest, stopping others."
    echo "$pids" | tail -n +2 | xargs -r kill -TERM 2>/dev/null || true
    sleep 2
  fi
  if pgrep -f "node TAMESSAGE/scripts/keepalive.js" > /dev/null 2>&1; then
    return 0
  fi
  setsid node "$KEEPALIVE" >> "$RUNS/keepalive.log" 2>&1 < /dev/null &
  sleep 2
}

log "Watchdog started."

while true; do
  # If keepalive not running and no recent submit in progress, restart
  if ! pgrep -f "node TAMESSAGE/scripts/keepalive.js" > /dev/null 2>&1 && ! pgrep -f "node $KEEPALIVE" > /dev/null 2>&1; then
    # Don't restart if submit just happened (wait for agent to fill new task)
    if [ -f "$RUNS/new_task.ready" ] && [ ! -f "$RUNS/current-answers.json" ]; then
      log "New task waiting for answers — keepalive paused."
    elif [ -f "$RUNS/submitted.flag" ] && [ -f "$RUNS/new_task.ready" ]; then
      log "New task ready — restarting keepalive for next TPT cycle."
      rm -f "$RUNS/submitted.flag"
      start_keepalive
    elif [ ! -f "$RUNS/submitted.flag" ]; then
      log "Keepalive dead — restarting."
      start_keepalive
    fi
  fi
  sleep "$INTERVAL"
done
