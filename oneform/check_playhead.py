import json
import urllib.request
import sys
from websocket import create_connection

def main():
    ports = [9233, 9232]
    pages = None
    for port in ports:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/json/list")
            with urllib.request.urlopen(req, timeout=5) as resp:
                pages = json.loads(resp.read())
                break
        except Exception: pass
    if not pages:
        print("Error connecting")
        sys.exit(1)
    page = [p for p in pages if p.get('type') == 'page' and "Annotation Tool" in p.get('title', '')][0]
    ws = create_connection(page['webSocketDebuggerUrl'], timeout=15)
    ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
    ws.recv()
    
    js = "document.querySelector('iframe').contentDocument.body.innerText"
    ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
    raw = ws.recv()
    data = json.loads(raw)
    result = data.get("result", {})
    if "exceptionDetails" in result:
        print("JS Error:", result["exceptionDetails"])
    else:
        val = result.get("result", {}).get("value")
        print("\n=== IFRAME TEXT ===")
        print(val)
        print("===================")
    ws.close()

if __name__ == "__main__":
    main()
