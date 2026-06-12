#!/bin/bash
# 看门狗：确保 auto_loop 始终运行（唯一 CDP 主控进程）
ROOT="/Users/xaa/zuoye/oneform/renzheng"
LOOP="$ROOT/TAMESSAGE/scripts/auto_loop.js"
LOG="$ROOT/TAMESSAGE/runs/watchdog.log"
PIDFILE="$ROOT/TAMESSAGE/runs/auto_loop.pid"
INTERVAL=20

mkdir -p "$ROOT/TAMESSAGE/runs"
log() { echo "[$(date -Iseconds)] $*" >> "$LOG"; }

log "loop_watchdog started."

while true; do
  if ! pgrep -f "node $LOOP" > /dev/null 2>&1 && ! pgrep -f "node TAMESSAGE/scripts/auto_loop.js" > /dev/null 2>&1; then
    log "auto_loop NOT running — restarting"
    # 停掉独立 keepalive，避免多 CDP 冲突
    pkill -f "node TAMESSAGE/scripts/keepalive.js" 2>/dev/null || true
    setsid node "$LOOP" >> "$ROOT/TAMESSAGE/runs/auto_loop.log" 2>&1 < /dev/null &
    sleep 3
    if pgrep -f "auto_loop.js" > /dev/null; then
      log "auto_loop restarted pid=$(pgrep -f 'auto_loop.js' | head -1)"
    else
      log "auto_loop restart FAILED"
    fi
  fi
  sleep "$INTERVAL"
done
