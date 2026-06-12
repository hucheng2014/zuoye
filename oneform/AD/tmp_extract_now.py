#!/usr/bin/env python3
import json, urllib.request
from websocket import create_connection

CDP = "http://browser:9223"
req = urllib.request.Request(f"{CDP}/json/list")
req.add_header("Host", "localhost:9222")
resp = urllib.request.urlopen(req, timeout=10)
pages = json.loads(resp.read())
page = [p for p in pages if p.get("type") == "page" and "tryrating" in p.get("url", "")][0]
ws_url = page["webSocketDebuggerUrl"].replace("ws://localhost:9222", "ws://browser:9223")
ws = create_connection(ws_url, timeout=15)
ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
ws.recv()

def evaluate(js):
    ws.send(json.dumps({"id": 99, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True, "awaitPromise": True}}))
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == 99:
            return data.get("result", {}).get("result", {}).get("value", "")

script = r"""(() => {
    var allData = {};
    document.querySelectorAll('iframe').forEach(function(iframe, i) {
        var srcdoc = iframe.getAttribute('srcdoc') || '';
        var taskMatch = srcdoc.match(/TaskAPI_Html_[^_]+_(01[A-Z0-9]+)/);
        var taskId = taskMatch ? taskMatch[1] : 'idx_' + i;
        var tplMatch = srcdoc.match(/TaskAPI_Html_([a-zA-Z0-9_-]+)_01/);
        var tplName = tplMatch ? tplMatch[1] : 'unknown';
        var decoded = srcdoc.replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
        decoded = decoded.replace(/<script[^>]*>[\s\S]*?<\/script>/gi,'').replace(/<style[^>]*>[\s\S]*?<\/style>/gi,'');
        var div = document.createElement('div');
        div.innerHTML = decoded;
        var text = (div.textContent || '').replace(/\s+/g,' ').trim();
        allData[taskId + '___' + tplName] = text.substring(0, 3000);
    });
    allData['__page__'] = (document.body.innerText || '').substring(0, 10000);
    return JSON.stringify(allData);
})()"""

data = json.loads(evaluate(script))
page_text = data.pop("__page__", "")
tasks = {}
for key, text in data.items():
    parts = key.split("___")
    if len(parts) == 2:
        tasks.setdefault(parts[0], {})[parts[1]] = text

print("PAGE_LINES:")
for line in page_text.split("\n"):
    if line.strip():
        print(line)
print(f"\nTASK_COUNT={len(tasks)}")
for i, (tid, tpls) in enumerate(sorted(tasks.items())):
    print(f"\n===TASK{i+1} ID={tid}===")
    for tpl, txt in sorted(tpls.items()):
        print(f"[{tpl}] {txt[:1500]}")
