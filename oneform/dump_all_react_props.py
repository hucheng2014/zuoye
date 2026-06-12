import json
import urllib.request
import sys
import os
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
                
    # JS code to serialize and return the first few layers of props
    dump_js = """
    (() => {
        let iframe = document.querySelector('iframe');
        if (!iframe) return JSON.stringify({ error: "No iframe found" });
        
        try {
            let doc = iframe.contentDocument || iframe.contentWindow.document;
            let root = doc.querySelector('#root') || doc.body;
            let keys = Object.keys(root);
            let containerKey = keys.find(k => k.startsWith('__reactContainer') || k.startsWith('__reactFiber'));
            if (!containerKey) return JSON.stringify({ error: "No React Container found" });
            
            let fiber = root[containerKey];
            
            // Serialize helper to avoid circular structures
            function getCleanObj(obj, maxDepth = 3) {
                let visited = new Set();
                
                function clean(o, depth = 0) {
                    if (depth > maxDepth || !o) return null;
                    if (typeof o !== 'object') return o;
                    if (visited.has(o)) return "[Circular]";
                    visited.add(o);
                    
                    if (Array.isArray(o)) {
                        return o.slice(0, 10).map(x => clean(x, depth + 1));
                    }
                    
                    let res = {};
                    try {
                        let keys = Object.keys(o);
                        // Filter out react internal keys like __reactFiber, __reactProps, _owner, etc.
                        keys = keys.filter(k => !k.startsWith('_') && k !== 'theme' && k !== 'history' && k !== 'navigation' && k !== 'router');
                        for (let k of keys.slice(0, 40)) {
                            let val = o[k];
                            let t = typeof val;
                            if (t === 'function') {
                                res[k] = "[Function]";
                            } else if (t === 'object') {
                                res[k] = clean(val, depth + 1);
                            } else {
                                res[k] = val;
                            }
                        }
                    } catch(e) {
                        res.error = e.message;
                    }
                    return res;
                }
                
                return clean(obj);
            }
            
            let data = {};
            let child = fiber;
            let layers = [];
            
            for (let i = 0; i < 6; i++) {
                if (!child) break;
                let layer_info = {
                    type: child.type ? (child.type.name || child.type.displayName || typeof child.type) : "unknown",
                    props: getCleanObj(child.memoizedProps, 3),
                    state: getCleanObj(child.memoizedState, 3)
                };
                layers.push(layer_info);
                child = child.child;
            }
            
            data.layers = layers;
            return JSON.stringify(data);
        } catch(e) {
            return JSON.stringify({ error: e.message });
        }
    })()
    """
    
    res_str = evaluate(dump_js)
    if res_str:
        res = json.loads(res_str)
        if "error" in res:
            print("Error:", res["error"])
        else:
            persist_dir = "/Users/xaa/zuoye/oneform/kuokka add"
            output_path = os.path.join(persist_dir, "react_structure.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2, ensure_ascii=False)
            print(f"Saved React tree props structure to {output_path}")
            
            # Print layer summaries
            for idx, layer in enumerate(res.get('layers', [])):
                print(f"\n--- LAYER {idx+1}: {layer['type']} ---")
                print("State keys:", list(layer['state'].keys()) if layer['state'] else "None")
                print("Props keys:", list(layer['props'].keys()) if layer['props'] else "None")
                
                # Check if tasks are visible
                if layer['props'] and 'tasks' in layer['props']:
                    print("  Found 'tasks' in props:")
                    print(json.dumps(layer['props']['tasks'], indent=2)[:500])
                    
    else:
        print("Search returned nothing.")
        
    ws.close()

if __name__ == "__main__":
    main()
