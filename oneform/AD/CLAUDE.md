# CLAUDE.md — Agent Instruction & Workflow Guide

This guide is designed for **Claude, Codex, oh-my-pi**, and other AI coding assistants operating in this workspace. It provides the exact commands, styling rules, and standard operating procedures (SOP) for Search Ads Relevance rating.

---

## 🛠 Project Commands & Scripts

Always run commands from `/app/AD` inside the `oneform-agent` container, or prepended with `docker exec -w /app/AD oneform-agent`.

### 1. Extract Current Page Information
Extract live details (Queries, Ad details, screenshot/iframe text) from TryRating via CDP:
```bash
docker exec oneform-agent python3 -c '
import json, urllib.request
from websocket import create_connection
CDP = "http://browser:9223"
req = urllib.request.Request(f"{CDP}/json/list")
req.add_header("Host", "localhost:9222")
resp = urllib.request.urlopen(req, timeout=5)
pages = json.loads(resp.read())
page = pages[0]
ws_url = page["webSocketDebuggerUrl"].replace("ws://localhost:9222", "ws://browser:9223")
ws = create_connection(ws_url, timeout=10)
ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
ws.recv()
def evaluate(js):
    ws.send(json.dumps({"id": 99, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True, "awaitPromise": True}}))
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == 99:
            return data.get("result", {}).get("result", {}).get("value", "")
js_extract = """(() => {
    let result = [];
    document.querySelectorAll("iframe").forEach((iframe, i) => {
        let text = "";
        try { text = iframe.contentDocument.body.innerText; } catch(e) { text = "Error"; }
        result.push({ index: i, text: text.substring(0, 1000) });
    });
    return JSON.stringify(result);
})()"""
print("URL:", evaluate("document.location.href"))
print("BODY TEXT:")
print(evaluate("document.body.innerText"))
print("IFRAME CONTENTS:")
print(json.dumps(json.loads(evaluate(js_extract)), indent=2, ensure_ascii=False))
'
```

### 2. Auto-Fill Form
Fill ratings and comments into the live browser form using React-compatible CDP websocket emulation:
```bash
docker exec -w /app/AD oneform-agent python3 /app/AD/fill_ad_page.py records/<file_name>.json
```

### 3. Verify & Submit Form
Perform post-fill checks, click the live "Submit Rating" button, verify there are no validation errors, and archive the submission time:
```bash
docker exec -w /app/AD oneform-agent python3 /app/AD/submit_ad_page.py records/<file_name>.json
```

---

## 📋 Rating & SOP Guidelines

To maintain excellent rating accuracy and avoid account bans, you **MUST** adhere to the following:

1. **Wait Time Constraint (Critical)**:
   - Always verify that **8 to 10 minutes** have elapsed since the previous submission timestamp (recorded in the `submit.submitted_at` section of the last JSON file) before calling `submit_ad_page.py`.
2. **Relevance Mapping**:
   - **Excellent**: The ad directly and fully satisfies the specific user search or is a direct synonym/identical brand competitor.
   - **Good**: Direct category competitors, close alternatives, or major platform substitutes (e.g. specialized mobile banking vs a different bank, general utility keyboards).
   - **Acceptable**: Broader utilities, different game styles with overlapping IP/developer ecosystems, or weak vertical associations (e.g., property B2B SaaS vs general B2C house listings).
   - **Bad**: Zero correlation, completely different domains, energy segments (EV car apps vs Sinopec gas stations), or unrelated genres. Explain **why** in detail.
3. **No Keyword Hard-Matching**:
   - Focus purely on user intent, app category, developer alignment, and visual evidence.
4. **Required Comments Format**:
   - Format: `[Query Intent] ... [Ad Analysis] ... [Relevance Breakdown] ... [Why not higher/lower] ... Rated [Rating].`
