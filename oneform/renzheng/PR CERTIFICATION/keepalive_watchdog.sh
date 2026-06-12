#!/bin/bash
# PR Certification watchdog — ensure exactly one keepalive.js, auto-restart on crash.
# Lifecycle flags in runs/:
#   ready.flag     — keepalive reached 12min, waiting for agent submit (do NOT restart)
#   submitted.flag — submit+next done, restart keepalive for next task
set -u
ROOT="/Users/xaa/zuoye/oneform/renzheng/PR CERTIFICATION"
KEEPALIVE="$ROOT/keepalive.js"
RUNS="$ROOT/runs"
LOG="$RUNS/watchdog.log"
INTERVAL=15
FAST_INTERVAL=2

mkdir -p "$RUNS"
log() { echo "[$(date -Iseconds)] $*" >> "$LOG"; }

count_keepalive() {
  pgrep -f "node $KEEPALIVE" 2>/dev/null | wc -l
}

start_keepalive() {
  local n
  n=$(count_keepalive)
  if [ "$n" -gt 1 ]; then
    log "Multiple keepalive ($n) — kill all, restart one."
    pkill -f "node $KEEPALIVE" 2>/dev/null || true
    sleep 2
  fi
  if pgrep -f "node $KEEPALIVE" > /dev/null 2>&1; then
    return 0
  fi
  log "Starting keepalive.js"
  setsid node "$KEEPALIVE" >> "$RUNS/keepalive.log" 2>&1 < /dev/null &
  sleep 2
  if pgrep -f "node $KEEPALIVE" > /dev/null; then
    log "keepalive started pid=$(pgrep -f "node $KEEPALIVE" | head -1)"
  else
    log "keepalive start FAILED"
  fi
}

log "Watchdog started."

while true; do
  n=$(count_keepalive)

  # ① TPT到了：立刻停保活并提交（不等待保活自己退出）
  if [ -f "$RUNS/ready.flag" ] && [ -f "$ROOT/current_ratings.json" ] && [ ! -f "$RUNS/submitting.flag" ]; then
    log "ready.flag + ratings ready — kill keepalive, submit NOW."
    pkill -f "node $KEEPALIVE" 2>/dev/null || true
    sleep 1
    date -Iseconds > "$RUNS/submitting.flag"
    node "$ROOT/submit_from_ratings.js" >> "$RUNS/submit.log" 2>&1 || log "Submit FAILED — see submit.log"
    rm -f "$RUNS/submitting.flag"
    log "Submit pipeline done."
  elif [ "$n" -gt 1 ]; then
    log "Dedup: $n keepalive processes"
    pkill -f "node $KEEPALIVE" 2>/dev/null || true
    sleep 2
    start_keepalive
  elif [ "$n" -eq 0 ]; then
    if [ -f "$RUNS/submitted.flag" ]; then
      log "submitted.flag — restart keepalive for next task."
      rm -f "$RUNS/ready.flag" "$RUNS/submitted.flag"
      start_keepalive
    elif [ ! -f "$RUNS/ready.flag" ]; then
      log "keepalive dead — restarting."
      start_keepalive
    fi
  fi

  if [ -f "$RUNS/ready.flag" ] && [ ! -f "$RUNS/submitting.flag" ]; then
    sleep "$FAST_INTERVAL"
  else
    sleep "$INTERVAL"
  fi
done
