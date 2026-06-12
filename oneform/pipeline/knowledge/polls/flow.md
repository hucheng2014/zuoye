# TA Intelligent Polls — Operation Flow

Target: ~290s per task (randomized 260-320s), daily <=7h, ~70 tasks, <10% inactive.
CDP: 127.0.0.1:9233 (fallback 9232) | VNC: 127.0.0.1:6082

## 7-Step Workflow

### Step 1: Extract Task
```bash
node "TA Intelligent Polls/scripts/session_guard.js" start    # first task of the day only
node "TA Intelligent Polls/scripts/extract_task.js" > "TA Intelligent Polls/runs/task-NNN-task.json"
```
- Connects to CDP, extracts current task data from page
- Must set viewport after connection: `page.setViewportSize({width: 1919, height: 1079})`
- Handle Task Overview popup: click Start button before interacting with form

### Step 2: Launch Keepalive
```bash
nohup node "TA Intelligent Polls/scripts/keepalive_lite.js" > /dev/null 2>&1 &
LITE_PID=$!
```
- Scrolls + moves mouse every 5-7s to prevent inactive accumulation during AI analysis
- MUST use nohup to prevent process death on shell exit
- Start IMMEDIATELY after extract_task.js exits (CDP released)

### Step 3: Analyze & Write answers.json
- Evaluate all 8 dimensions independently per SOP scoring rules
- Output: `TA Intelligent Polls/runs/task-NNN-answers.json`
- Keepalive runs in background throughout this step (~2-3 min)

### Step 4: Kill Keepalive + Dry-Run
```bash
kill $LITE_PID
node "TA Intelligent Polls/scripts/fill_task.js" --answers "TA Intelligent Polls/runs/task-NNN-answers.json" --dry-run
```
- Verify answer mapping before actual form fill
- Only one CDP script at a time -- keepalive MUST be killed first

### Step 5: Fill Form + Validate
```bash
node "TA Intelligent Polls/scripts/fill_task.js" --answers "TA Intelligent Polls/runs/task-NNN-answers.json"
node "TA Intelligent Polls/scripts/check_form.js"
```
- Confirm ALL radio groups have selections, no validation errors
- Fix any missed selections immediately
- NEVER skip any question or use Skip Current Task

### Step 6: Launch Bridge Timer
```bash
nohup node "TA Intelligent Polls/scripts/bridge.js" > "TA Intelligent Polls/runs/bridge.log" 2>&1 &
BRIDGE_PID=$!
```
- Auto-randomizes target between 260-320s
- Scrolls every 3-5s with jitter for keepalive
- Injects 1 deliberate reading pause of 12-15s (simulates human review)
- MUST use nohup with log redirect
- NEVER start during fill_task.js execution

### Step 7: Monitor Bridge + Submit + Next
```bash
tail -f "TA Intelligent Polls/runs/bridge.log"
# Wait for "READY TO SUBMIT", then Ctrl+C
node "TA Intelligent Polls/scripts/full_submit.js"
```
Post-submit verification:
- Confirm dialog appears (#starshot_submit_task_button)
- After clicking confirm, check timer disappears/resets to 0
- If timer still running = submission failed, retry
- On success:
```bash
node "TA Intelligent Polls/scripts/click_next.js"
node "TA Intelligent Polls/scripts/session_guard.js" task
```

## Timeline (~290s example)
```
0:00   extract_task.js (~10s)                              Active
0:10   keepalive_lite.js + AI analysis (~150s)             Active
2:40   kill keepalive + fill_task.js (~30s)                Active
3:10   check_form.js (~15s)                                Active
3:25   bridge.js (target 260-320s, 1x pause 12-15s)       Active + ~13.5s Inactive
~7:55  full_submit.js (~20s)                               Active
~8:15  click_next.js -> next task                          Active
```
Inactive total: ~22s (script gaps ~8s + bridge pause ~13.5s) = ~8% of Active < 10% threshold

## End-of-Day Checklist
```bash
node "TA Intelligent Polls/scripts/session_guard.js" status
ps aux | grep -E "[b]ridge|[k]eepalive"    # kill any residual processes
node "TA Intelligent Polls/scripts/session_guard.js" stop
```

## Failure Handling
- Same step fails 2x consecutively: stop retrying, diagnose root cause
- CDP connection / login / captcha issues: notify user to open VNC immediately
