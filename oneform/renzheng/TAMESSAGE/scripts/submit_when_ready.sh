#!/bin/bash
# Wait for page active timer >= 540s (9min), then stop keepalive and submit.
set -e
cd /Users/xaa/zuoye/oneform/renzheng
ANSWERS="TAMESSAGE/runs/current-answers.json"
TARGET="${TAMESSAGE_SUBMIT_AT:-540}"
LOG="TAMESSAGE/runs/submit.log"

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

log "Waiting for active timer >= ${TARGET}s..."

while true; do
  # Brief pause keepalive to read timer (only one CDP client)
  if [ -f TAMESSAGE/runs/keepalive.pid ]; then
    kill -TERM "$(cat TAMESSAGE/runs/keepalive.pid)" 2>/dev/null || true
    sleep 2
  fi
  SEC=$(node -e "
    const {chromium}=require('playwright');
    (async()=>{
      const b=await chromium.connectOverCDP('http://127.0.0.1:9233');
      const p=b.contexts()[0].pages().find(x=>x.url().includes('starshot'));
      const t=await p.locator('body').innerText();
      const m=t.match(/(\d+)s/);
      console.log(m?m[1]:0);
      await b.close();
    })().catch(()=>console.log(0));
  " 2>/dev/null)
  log "Timer: ${SEC}s / ${TARGET}s"
  if [ "$SEC" -ge "$TARGET" ] 2>/dev/null; then
    break
  fi
  # Restart keepalive between checks
  setsid node TAMESSAGE/scripts/keepalive.js >> TAMESSAGE/runs/keepalive.log 2>&1 < /dev/null &
  sleep 30
done

log "Timer reached. Submitting..."
if [ -f TAMESSAGE/runs/keepalive.pid ]; then
  kill -TERM "$(cat TAMESSAGE/runs/keepalive.pid)" 2>/dev/null || true
  sleep 2
fi
node TAMESSAGE/scripts/fill_task.js --answers "$ANSWERS" --submit >> "$LOG" 2>&1
log "Submit script finished."
