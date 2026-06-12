#!/bin/bash
# 做题结束：停所有后台 + 关闭 starshot 标签页（不关会一直计非活跃）
ROOT="/Users/xaa/zuoye/oneform/renzheng/PR CERTIFICATION"
LOG="$ROOT/runs/shutdown.log"
log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

log "=== shutdown_all start ==="

# 1. 停所有做题相关进程
for pat in task_bridge.js auto_grade_daemon.js "PR CERTIFICATION/keepalive" keepalive_watchdog auto_finish_after_n auto_finish_after_two finish_two_and_stop wait_submit; do
  pkill -f "$pat" 2>/dev/null && log "killed: $pat" || true
done
sleep 1

# 2. 清理 pid 文件
rm -f "$ROOT/runs/bridge.pid" "$ROOT/runs/submit.pid" 2>/dev/null

# 3. 必须关闭 starshot 标签页
cd "$ROOT" && node -e "
const puppeteer=require('puppeteer-core');
const {CDP_URL,CDP_FALLBACK}=require('./config');
(async()=>{
  let b;
  for (const url of [CDP_URL,CDP_FALLBACK]) {
    try { b=await puppeteer.connect({browserURL:url,defaultViewport:null}); break; } catch {}
  }
  if (!b) { console.log('no CDP'); return; }
  const pages=await b.pages();
  let n=0;
  for (const p of pages) {
    if (p.url().includes('starshot')) { await p.close(); n++; console.log('closed:', p.url().slice(0,80)); }
  }
  if (!n) console.log('no starshot tab');
  await b.disconnect();
})().catch(e=>console.error(e.message));
" 2>>"$LOG" | tee -a "$LOG"

log "=== shutdown_all done ==="
pgrep -af "task_bridge|auto_grade|keepalive|auto_finish" 2>/dev/null | grep -v sandbox | tee -a "$LOG" || log "no remaining processes"
