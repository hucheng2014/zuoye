#!/bin/bash
# 再等 N 次 SUCCESS total 后执行 shutdown_all（停 bridge/daemon + 关闭 starshot 标签页）
# 用法: ./auto_finish_after_n.sh 4   # 当前题已算第1题时，再等4题
set -u
ROOT="/Users/xaa/zuoye/oneform/renzheng/PR CERTIFICATION"
LOG="$ROOT/runs/auto_finish.log"
SUBMIT_LOG="$ROOT/runs/submit.log"
NEED="${1:-4}"

count_success() {
  grep -c "SUCCESS total" "$SUBMIT_LOG" 2>/dev/null || echo 0
}

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

BASELINE="$(count_success)"
TARGET=$((BASELINE + NEED))

log "=== auto_finish_after_n: baseline=$BASELINE need=$NEED target=$TARGET ==="
log "收尾动作: shutdown_all → pkill bridge/daemon → 关闭 Annotation Tool (starshot) 标签页"

for i in $(seq 1 120); do
  sleep 30
  c="$(count_success)"
  if [ "$((i % 4))" -eq 0 ] || [ "$c" -ge "$((TARGET - 1))" ]; then
    log "poll $i: success=$c / $TARGET"
  fi
  if [ "$c" -ge "$TARGET" ]; then
    log "达到 $TARGET 次提交 — 执行 shutdown_all"
    bash "$ROOT/shutdown_all.sh"
    exit 0
  fi
done

log "TIMEOUT(60min) — 强制执行 shutdown_all 避免非活跃挂机"
bash "$ROOT/shutdown_all.sh"
exit 1
