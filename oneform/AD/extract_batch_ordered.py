#!/usr/bin/env python3
"""Extract current TryRating AD page tasks in page order as JSON."""
import json
import re
import urllib.request
from websocket import create_connection

CDP = "http://browser:9223"
req = urllib.request.Request(f"{CDP}/json/list")
req.add_header("Host", "localhost:9222")
pages = json.loads(urllib.request.urlopen(req, timeout=10).read())
page = [p for p in pages if p.get("type") == "page" and "tryrating" in p.get("url", "")][0]
ws_url = page["webSocketDebuggerUrl"].replace("ws://localhost:9222", "ws://browser:9223")
ws = create_connection(ws_url, timeout=15)
ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
ws.recv()


def evaluate(js):
    ws.send(json.dumps({"id": 99, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
    while True:
        data = json.loads(ws.recv())
        if data.get("id") == 99:
            return data.get("result", {}).get("result", {}).get("value", "")


body = evaluate("document.body.innerText || ''")
lines = [l.strip() for l in body.split("\n") if l.strip()]

tasks = []
i = 0
while i < len(lines):
    if lines[i] == "Request ID" and i + 1 < len(lines):
        req_id = lines[i + 1]
        query = ""
        for j in range(i + 2, min(i + 20, len(lines))):
            if lines[j] == "Web search for query:":
                break
            if lines[j] not in ("QUERY", "RESULT AD", "Ad Relevance", "Excellent", "Good", "Acceptable", "Bad", "Comments"):
                if not query and lines[j] not in ("Request ID",):
                    query = lines[j]
        tasks.append({"task_id": req_id, "query": query, "index": len(tasks) + 1})
    i += 1

ad_js = r"""(() => {
  const ads = [];
  document.querySelectorAll('iframe').forEach((iframe) => {
    const srcdoc = iframe.getAttribute('srcdoc') || '';
    if (!srcdoc.includes('lRBFmJuyo')) return;
    const decoded = srcdoc.replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
    const div = document.createElement('div');
    div.innerHTML = decoded.replace(/<script[^>]*>[\s\S]*?<\/script>/gi,'');
    const text = (div.textContent || '').replace(/\s+/g,' ').trim();
    const dev = text.match(/Developer:\s*(.+?)(?:\s+Ad|\s*$)/i);
    const ad = text.match(/^(.+?)\s+Ad\s+/);
    ads.push({
      name: ad ? ad[1].trim() : text.slice(0,80),
      developer: dev ? dev[1].trim() : '',
      full: text.slice(0, 500)
    });
  });
  return JSON.stringify(ads);
})()"""

ads = json.loads(evaluate(ad_js))
for t, ad in zip(tasks, ads):
    t["ad"] = ad

print(json.dumps({"tasks": tasks}, ensure_ascii=False, indent=2))
