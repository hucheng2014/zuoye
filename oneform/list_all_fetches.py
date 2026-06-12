import json
import urllib.request
import sys
from websocket import create_connection

def main():
    ports = [9233, 9232]
    pages = None
    
    for port in ports:
        cdp_url = f"http://127.0.0.1:{port}"
        try:
            req = urllib.request.Request(f"{cdp_url}/json/list")
            with urllib.request.urlopen(req, timeout=5) as resp:
                pages = json.loads(resp.read())
                break
        except Exception:
            pass
            
    if not pages:
        print("Error: Could not connect to CDP.")
        sys.exit(1)
        
    page = [p for p in pages if p.get('type') == 'page' and "Annotation Tool" in p.get('title', '')][0]
    ws_url = page['webSocketDebuggerUrl']
    ws = create_connection(ws_url, timeout=15)
    
    ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
    ws.recv()
    
    def evaluate(js_expr):
        payload = {
            "id": 100,
            "method": "Runtime.evaluate",
            "params": {
                "expression": js_expr,
                "returnByValue": True,
                "awaitPromise": True
            }
        }
        ws.send(json.dumps(payload))
        while True:
            raw = ws.recv()
            data = json.loads(raw)
            if data.get("id") == 100:
                res = data.get("result", {})
                if "exceptionDetails" in res:
                    print("JS Error:", res["exceptionDetails"])
                    return None
                return res.get("result", {}).get("value")
                
    # Fetch all resources
    resources_js = """
    (() => {
        let entries = performance.getEntries();
        return JSON.stringify(entries.map(e => ({
            name: e.name,
            initiatorType: e.initiatorType || 'unknown',
            duration: e.duration || 0
        })));
    })()
    """
    
    entries_str = evaluate(resources_js)
    if entries_str:
        entries = json.loads(entries_str)
        print(f"Total entries: {len(entries)}")
        print("\n=== FETCH / XMLHTTPREQUEST ENTRIES ===")
        fetch_entries = [e for e in entries if e['initiatorType'] in ['fetch', 'xmlhttprequest']]
        for e in fetch_entries:
            print(f"- [{e['initiatorType']}] {e['name']} (duration: {e['duration']:.2f}ms)")
    else:
        print("Could not retrieve entries.")
        
    ws.close()

if __name__ == "__main__":
    main()
