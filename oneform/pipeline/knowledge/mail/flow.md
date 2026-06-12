# Mail Smart Reply (MSR) -- Operation Flow

Target: >=8min per task, daily <=7h, ~40 tasks, <10% inactive.
CDP: 127.0.0.1:9233 (fallback 9232) | VNC: 127.0.0.1:6082

## 6-Step Workflow

### Step 1: Verify CDP
```bash
curl -sS http://127.0.0.1:9233/json/version
```
- If 9233 fails, try 9232 as backup
- Login/captcha/permission popup -> stop, notify user to open VNC at 127.0.0.1:6082

### Step 2: Extract Task
```bash
node MAIL/scripts/extract_task.js > MAIL/runs/current-task.json
```
- Connects to CDP, extracts: Prompt, Previous Mail, Response A, Response B, User Profile, Additional Personal Info
- Must set viewport after connection: `page.setViewportSize({width: 1919, height: 1079})`

### Step 3: Grade Per grading.md (8-Step Per-Response Evaluation)
For each response (A and B), evaluate in order:
1. Harmfulness
2. Subject Line / Generic Quality checkboxes
3. Groundedness (check ALL Additional Info fields first)
4. Instruction Adherence & Contextual Fit
5. Tone & Empathy Alignment
6. Naturalness
7. Localization (locale-specific punctuation/format)
8. Personalization (compare against User Profile)

Then: Pairwise Comparison + short English observation noting key differences.

### Step 4: Dry-Run Fill
```bash
node MAIL/scripts/fill_task.js --answers MAIL/runs/current-answers.json --dry-run
```
- Verify answer mapping before actual form fill
- Only one CDP script at a time

### Step 5: Submit
```bash
node MAIL/scripts/fill_task.js --answers MAIL/runs/current-answers.json --submit
```
- Confirm all required fields are selected before submission
- Verify submission success on result page

### Step 6: Next Task
```bash
node MAIL/scripts/next_task.js
```
- If "Do not ask for confirmation again" checkbox appears, check it first then click Next Task
- If "there are no available tasks at the moment" appears, stop and save state

## Data Read Order (per task)
1. User Prompt (what the sender wants to reply)
2. Previous Mail (the incoming email being replied to)
3. Response A and Response B (two draft replies to evaluate)
4. User Profile (sender's writing style traits)
5. Additional Personal Info (supplementary facts -- MUST check before grading)

## Failure Handling
- Same step fails 2x consecutively: stop retrying, diagnose root cause
- CDP connection / login / captcha issues: notify user to open VNC immediately
- Never use Skip Current Task
