import json, sys, time, re

def rpc(method, params=None, ws_session_id=None):
    req = {"id": 1, "method": method}
    if params: req["params"] = params
    if ws_session_id: req["sessionId"] = ws_session_id
    return json.dumps(req)

def send(cmd):
    with open("/tmp/cdp_in", "w") as f:
        f.write(cmd + "\n")
    time.sleep(3)
    out = ""
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            with open("/tmp/cdp_out", "r") as f:
                out = f.read()
            if out.strip():
                lines = out.strip().split("\n")
                json_lines = [l for l in lines if l.strip().startswith("{")]
                if json_lines:
                    return json_lines[-1]
        except: pass
        time.sleep(0.5)
    return out

# Get page title
print("=== PAGE TITLE ===")
resp = send(rpc("Runtime.evaluate", {"expression": "document.title", "returnByValue": True}))
try:
    data = json.loads(resp) if isinstance(resp, str) else resp
    if "result" in data:
        print(data["result"]["result"]["value"])
    else:
        print(resp[:200])
except Exception as e:
    print("ERR:", e)

# Extract all task cards with detailed info
js = """
(() => {
    let tasks = [];
    document.querySelectorAll('.ant-card').forEach((card, i) => {
        let text = card.innerText.substring(0, 1500);
        let links = [];
        card.querySelectorAll('a').forEach(a => {
            let href = a.getAttribute('href') || '';
            let linkText = a.innerText.substring(0, 200);
            if (href || linkText) {
                links.push({text: linkText, href: href});
            }
        });
        tasks.push({index: i, text: text, links: links});
    });
    return JSON.stringify(tasks);
})();
"""
print("\n=== TASK DETAILS ===")
resp = send(rpc("Runtime.evaluate", {"expression": js, "returnByValue": True}))
try:
    data = json.loads(resp) if isinstance(resp, str) else resp
    tasks = json.loads(data["result"]["result"]["value"])
    for t in tasks:
        print(f"\n--- Task {t['index']} ---")
        print("TEXT:", t['text'][:800])
        print("LINKS:", json.dumps(t['links'][:3], ensure_ascii=False))
except Exception as e:
    print("ERROR:", e, resp[:500] if resp else "no resp")
