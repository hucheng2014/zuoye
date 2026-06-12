#!/bin/bash
# 达到收尾条件：等第 11 条 SUCCESS → 调用 shutdown_all（必关 starshot 标签 + 停所有后台）
ROOT="/Users/xaa/zuoye/oneform/renzheng/PR CERTIFICATION"
LOG="$ROOT/runs/auto_finish.log"
log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

count_success() {
  grep -c "SUCCESS total" "$ROOT/runs/submit.log" 2>/dev/null || echo 0
}

TARGET=$(($(count_success) + 1))
log "=== auto_finish: wait SUCCESS count $TARGET ==="

for i in $(seq 1 30); do
  sleep 30
  c=$(count_success)
  log "poll $i: count=$c target=$TARGET"
  if [ "$c" -ge "$TARGET" ]; then
    log "submit detected — running shutdown_all"
    bash "$ROOT/shutdown_all.sh"
    exit 0
  fi
done

log "TIMEOUT — still running shutdown_all to stop inactive timer"
bash "$ROOT/shutdown_all.sh"
