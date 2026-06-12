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
                
    # JS code to inspect iframe react tree
    react_js = """
    (() => {
        let results = {};
        let iframe = document.querySelector('iframe');
        if (!iframe) return JSON.stringify({ error: "No iframe found" });
        
        try {
            let doc = iframe.contentDocument || iframe.contentWindow.document;
            let root = doc.querySelector('#root') || doc.body;
            results.root_id = root.id;
            results.root_class = root.className;
            
            // Check keys of root
            let keys = Object.keys(root);
            results.root_keys = keys;
            
            let fiberKey = keys.find(k => k.startsWith('__reactContainer') || k.startsWith('__reactFiber'));
            if (!fiberKey) {
                // Try child elements
                let firstChild = root.firstElementChild;
                if (firstChild) {
                    keys = Object.keys(firstChild);
                    results.child_keys = keys;
                    fiberKey = keys.find(k => k.startsWith('__reactFiber') || k.startsWith('__reactProps') || k.startsWith('__reactEvents'));
                    if (fiberKey) {
                        root = firstChild;
                    }
                }
            }
            
            if (fiberKey) {
                results.matched_key = fiberKey;
                let fiber = root[fiberKey];
                
                // Helper to search properties in the fiber tree
                let visited = new Set();
                let found_props = [];
                
                function search(obj, path = "", depth = 0) {
                    if (!obj || depth > 5 || visited.has(obj)) return;
                    visited.add(obj);
                    
                    try {
                        let keys = Object.keys(obj);
                        for (let k of keys) {
                            let val = obj[k];
                            let currentPath = path ? `${path}.${k}` : k;
                            
                            // Check if property name contains target words
                            let kl = k.toLowerCase();
                            if (kl.includes('task') || kl.includes('audio') || kl.includes('prop') || kl.includes('config') || kl.includes('state')) {
                                let valType = typeof val;
                                if (valType === 'string' || valType === 'number' || valType === 'boolean') {
                                    found_props.push({ path: currentPath, value: val });
                                } else {
                                    found_props.push({ path: currentPath, value: `[Object ${valType}]` });
                                }
                            }
                            
                            if (val && typeof val === 'object') {
                                search(val, currentPath, depth + 1);
                            }
                        }
                    } catch(e) {}
                }
                
                search(fiber, "fiber");
                results.found_props = found_props.slice(0, 50);
            } else {
                results.matched_key = "None";
            }
            
            return JSON.stringify(results);
        } catch(e) {
            return JSON.stringify({ error: e.message });
        }
    })()
    """
    
    res_str = evaluate(react_js)
    if res_str:
        res = json.loads(res_str)
        if "error" in res:
            print("Error:", res["error"])
        else:
            print("Root id/class:", res.get("root_id"), res.get("root_class"))
            print("Root keys:", res.get("root_keys"))
            print("Matched key:", res.get("matched_key"))
            if "child_keys" in res:
                print("Child keys:", res.get("child_keys"))
            print("\nFound properties:")
            for p in res.get("found_props", []):
                print(f"- {p['path']}: {p['value']}")
    else:
        print("Search returned nothing.")
        
    ws.close()

if __name__ == "__main__":
    main()
