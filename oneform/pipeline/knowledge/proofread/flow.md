# Proofread V2 -- Operation Flow

Target: >=12min (720s) per task, daily <=7.5h, 25-28 tasks, <10% inactive.
CDP: 127.0.0.1:9233 (fallback 9232) | VNC: 127.0.0.1:6082

## 8-Step Workflow

### Step 1: Extract Task
```bash
node PROOFREAD/scripts/extract_task.js > PROOFREAD/runs/task-NNN-task.json
```
- Connects to CDP, extracts input text + 3 responses (A, B, C)
- Must set viewport after connection: `page.setViewportSize({width: 1919, height: 1079})`
- Task Overview modal may appear -- click Start button to dismiss before anything else

### Step 2: Launch Keepalive Immediately
```bash
nohup node PROOFREAD/scripts/keepalive_lite.js > /dev/null 2>&1 &
LITE_PID=$!
```
- Scrolls main page + mouse movement every ~6s
- Does NOT switch iframe tabs -- safe during analysis
- CRITICAL: eliminates inactive time during AI analysis (5-8 min)

### Step 3: Analyze + Write answers.json + judgement.md
- Read input text, classify formality, identify all objective errors
- Evaluate each response (A, B, C) independently: Q1 -> Q2 -> Q3 -> Q4
- Apply Minimal Edit Principle + formality-aware three-level error framework
- Write `PROOFREAD/runs/task-NNN-answers.json` and `task-NNN-judgement.md`
- Each dimension must be independent -- do not let one pollute another

### Step 4: Kill Keepalive -> Dry-Run Fill
```bash
kill $LITE_PID
node PROOFREAD/scripts/fill_task.js --answers PROOFREAD/runs/task-NNN-answers.json --dry-run
```
- Verify answer mapping before actual form fill
- Only one CDP script at a time

### Step 5: Formal Fill + Validate (must reach 3/3 Complete)
```bash
node PROOFREAD/scripts/fill_task.js --answers PROOFREAD/runs/task-NNN-answers.json
node PROOFREAD/scripts/check_tabs.js
```
- Must confirm Response A/B/C all show `3/3 Complete` and `0 errors`
- Dynamic form trap: when `correctness = some_unnecessary`, extra checkbox group renders (formatting/mechanical/core_content) -- fill_task.js cannot fill these, must manually switch to Response tab and force-click
- Pre-checked residual: fill_task only adds, never unchecks -- verify no stale checkboxes from previous task
- If any gap found: fix and re-run check_tabs.js until all green

### Step 6: Launch bridge.js for 720s Timer
```bash
nohup node PROOFREAD/scripts/bridge.js > PROOFREAD/runs/bridge.log 2>&1 &
BRIDGE_PID=$!
```
- Auto-cycles Response tabs + scrolls every ~4s for keepalive
- Auto-handles Next Task / Start popups
- NEVER start bridge.js while fill_task.js is running

### Step 7: Monitor Bridge Every Minute
```bash
tail -3 PROOFREAD/runs/bridge.log && ps aux | grep "[b]ridge.js"
```
- Report: bridge PID, current timer seconds, seconds remaining to 720s

### Step 8: Kill Bridge -> Submit
```bash
kill $BRIDGE_PID
node PROOFREAD/scripts/full_submit.js
```
- After Submit: wait for confirmation dialog (#starshot_submit_task_button)
- After confirmation: verify timer disappears/resets to 0 = success
- If timer still running = submission failed, retry
- Do NOT check for Next Task before confirming submission
- After success: click "Next Task" button, record task count:
```bash
node PROOFREAD/scripts/session_guard.js task
```

## Timeline (single task ~15 min)
```
0:00  extract_task.js (~10s)
0:10  keepalive_lite.js start -- AI analysis (5-8 min)
7:00  kill keepalive -> fill_task.js (~60s)
8:00  check_tabs.js (~30s)
8:30  bridge.js start -- wait for elapsed >= 720s
14:00 bridge.js auto-exit
14:00 full_submit.js (~30s) -> Next Task -> next
```

## Daily Limits
| Metric | Safe | Danger |
|--------|------|--------|
| Daily total hours | <=7.5h | >8h |
| Inactive ratio | <10% | >30% |
| Daily task count | 25-28 | >35 |
| Min time per task | >=12min | <10min |

## Failure Handling
- Same step fails 2x: stop retrying, diagnose root cause
- CDP / login / captcha: notify user to open VNC immediately
- Never use Skip Current Task
