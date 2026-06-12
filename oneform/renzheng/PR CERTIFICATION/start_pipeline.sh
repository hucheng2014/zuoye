#!/bin/bash
# 启动完整 PR 流水线：task_bridge（保活+提交）+ ratings_watchdog（判分状态监控，无 LLM）
set -u
ROOT="/Users/xaa/zuoye/oneform/renzheng/PR CERTIFICATION"
RUNS="$ROOT/runs"
BRIDGE="$ROOT/task_bridge.js"
DAEMON="$ROOT/auto_grade_daemon.js"
BRIDGE_LOG="$RUNS/bridge.log"
DAEMON_LOG="$RUNS/grade_daemon.log"

mkdir -p "$RUNS"

pkill -f "node $ROOT/keepalive.js" 2>/dev/null || true
pkill -f "keepalive_watchdog.sh" 2>/dev/null || true
pkill -f "node $BRIDGE" 2>/dev/null || true
pkill -f "node $DAEMON" 2>/dev/null || true
sleep 2

start_one() {
  local label="$1" script="$2" log="$3"
  if pgrep -f "node $script" > /dev/null 2>&1; then
    echo "$label already running pid=$(pgrep -f "node $script" | head -1)"
    return 0
  fi
  setsid node "$script" >> "$log" 2>&1 < /dev/null &
  sleep 2
  if pgrep -f "node $script" > /dev/null; then
    echo "$label started pid=$(pgrep -f "node $script" | head -1) log=$log"
  else
    echo "FAILED to start $label"
    return 1
  fi
}

start_one "task_bridge" "$BRIDGE" "$BRIDGE_LOG"
start_one "ratings_watchdog" "$DAEMON" "$DAEMON_LOG"

echo "Pipeline up. Closed-loop: ensure_ratings.js on extract + overdue retry (grade_task fallback)."
