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
                
    # Inspect window keys and Redux state if available
    deep_js = """
    (() => {
        let results = {};
        
        // Check window state
        let keys = Object.keys(window);
        results.interesting_keys = keys.filter(k => {
            let l = k.toLowerCase();
            return l.includes('store') || l.includes('redux') || l.includes('state') || l.includes('task') || l.includes('config') || l.includes('data');
        });
        
        // Try to dump localStorage and sessionStorage
        results.localStorage = {};
        try {
            for (let i = 0; i < localStorage.length; i++) {
                let k = localStorage.key(i);
                results.localStorage[k] = localStorage.getItem(k).substring(0, 1000);
            }
        } catch(e) { results.localStorage_error = e.message; }
        
        results.sessionStorage = {};
        try {
            for (let i = 0; i < sessionStorage.length; i++) {
                let k = sessionStorage.key(i);
                results.sessionStorage[k] = sessionStorage.getItem(k).substring(0, 1000);
            }
        } catch(e) { results.sessionStorage_error = e.message; }
        
        // Try to find Redux store state
        results.redux_state = "Not found";
        try {
            // Find any elements with react properties (fiber)
            let root = document.querySelector('#root') || document.body;
            let fiberKey = Object.keys(root).find(k => k.startsWith('__reactContainer') || k.startsWith('__reactFiber'));
            if (fiberKey) {
                results.fiber_key = fiberKey;
                // We can traverse the fiber tree to find store or state
                let fiber = root[fiberKey];
                results.fiber_state = "Traversing fiber...";
                
                // Let's search window for store
                if (window.store) {
                    results.redux_state = window.store.getState();
                } else if (window.__redux_store__) {
                    results.redux_state = window.__redux_store__.getState();
                }
            }
        } catch(e) { results.fiber_error = e.message; }
        
        return JSON.stringify(results);
    })()
    """
    
    res_str = evaluate(deep_js)
    if res_str:
        res = json.loads(res_str)
        print("\n=== INTERESTING KEYS ===")
        print(res.get('interesting_keys'))
        print("\n=== LOCAL STORAGE ===")
        print(json.dumps(res.get('localStorage'), indent=2))
        print("\n=== SESSION STORAGE ===")
        print(json.dumps(res.get('sessionStorage'), indent=2))
        print("\n=== REDUX STATE ===")
        print(json.dumps(res.get('redux_state'), indent=2))
    else:
        print("Failed to run deep inspect JS.")
        
    ws.close()

if __name__ == "__main__":
    main()
