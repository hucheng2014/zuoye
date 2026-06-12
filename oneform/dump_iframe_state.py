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
                
    # Inspect all keys in the iframe window
    search_js = """
    (() => {
        let results = {};
        let iframe = document.querySelector('iframe');
        if (!iframe) return JSON.stringify({ error: "No iframe found" });
        
        try {
            let win = iframe.contentWindow;
            let keys = Object.keys(win);
            results.all_keys = keys;
            
            // Look for interesting keys
            let interesting = keys.filter(k => {
                let l = k.toLowerCase();
                return l.includes('audio') || l.includes('wave') || l.includes('player') || l.includes('plugin') || l.includes('state') || l.includes('store') || l.includes('data') || l.includes('task');
            });
            results.interesting = interesting;
            
            // Check some specific potential variables
            for (let k of interesting) {
                try {
                    let val = win[k];
                    let t = typeof val;
                    if (t === 'string' || t === 'number' || t === 'boolean') {
                        results[k] = val;
                    } else {
                        results[k] = `[Object type ${t}]`;
                    }
                } catch(e) {
                    results[k + "_err"] = e.message;
                }
            }
            
            return JSON.stringify(results);
        } catch(e) {
            return JSON.stringify({ error: e.message });
        }
    })()
    """
    
    res_str = evaluate(search_js)
    if res_str:
        res = json.loads(res_str)
        if "error" in res:
            print("Error:", res["error"])
        else:
            print("All Iframe window keys:", res.get("all_keys"))
            print("\nInteresting Iframe window keys:", res.get("interesting"))
            print("\nValues:")
            for k in res.get("interesting", []):
                print(f"- {k}: {res.get(k)}")
    else:
        print("Search returned nothing.")
        
    ws.close()

if __name__ == "__main__":
    main()
