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
                
    # JS code to deep search the React tree for task payload
    react_search_js = """
    (() => {
        let iframe = document.querySelector('iframe');
        if (!iframe) return JSON.stringify({ error: "No iframe found" });
        
        try {
            let doc = iframe.contentDocument || iframe.contentWindow.document;
            let root = doc.querySelector('#root') || doc.body;
            let keys = Object.keys(root);
            let containerKey = keys.find(k => k.startsWith('__reactContainer') || k.startsWith('__reactFiber'));
            if (!containerKey) return JSON.stringify({ error: "No React Container key found" });
            
            let fiber = root[containerKey];
            
            // We want to traverse all fiber nodes
            let visited = new Set();
            let task_payloads = [];
            
            function traverseFiber(node) {
                if (!node || visited.has(node)) return;
                visited.add(node);
                
                // Inspect memoizedProps and memoizedState
                let props = node.memoizedProps;
                let state = node.memoizedState;
                
                // Helper to check if an object looks like a task payload
                function checkObj(obj, label) {
                    if (!obj || typeof obj !== 'object') return;
                    
                    // Starshot tasks usually have properties like 'task', 'payload', 'schema', 'data', 'audio'
                    if (obj.task && typeof obj.task === 'object' && (obj.task.id || obj.task.data)) {
                        task_payloads.push({ label: label, type: "direct_task", data: obj.task });
                    }
                    if (obj.taskPayload && typeof obj.taskPayload === 'object') {
                        task_payloads.push({ label: label, type: "task_payload", data: obj.taskPayload });
                    }
                    if (obj.data && typeof obj.data === 'object' && obj.data.signals) {
                        task_payloads.push({ label: label, type: "task_signals", data: obj.data });
                    }
                    if (obj.signals && typeof obj.signals === 'object') {
                        task_payloads.push({ label: label, type: "signals", data: obj.signals });
                    }
                }
                
                if (props) {
                    checkObj(props, "props");
                    // Traverse props keys
                    try {
                        for (let k in props) {
                            if (props[k] && typeof props[k] === 'object') {
                                checkObj(props[k], "props." + k);
                            }
                        }
                    } catch(e) {}
                }
                
                if (state) {
                    checkObj(state, "state");
                    // Traverse state keys or memoizedState list
                    try {
                        let cur = state;
                        while (cur) {
                            if (cur.memoizedState && typeof cur.memoizedState === 'object') {
                                checkObj(cur.memoizedState, "state.memoizedState");
                            }
                            cur = cur.next;
                        }
                    } catch(e) {}
                }
                
                // Traverse children
                if (node.child) traverseFiber(node.child);
                if (node.sibling) traverseFiber(node.sibling);
            }
            
            traverseFiber(fiber);
            
            return JSON.stringify({
                found_count: task_payloads.length,
                payloads: task_payloads
            });
        } catch(e) {
            return JSON.stringify({ error: e.message });
        }
    })()
    """
    
    res_str = evaluate(react_search_js)
    if res_str:
        res = json.loads(res_str)
        if "error" in res:
            print("Error:", res["error"])
        else:
            print(f"Found {res.get('found_count')} task payloads in React tree:")
            persist_dir = "/Users/xaa/zuoye/oneform/kuokka add"
            for i, p in enumerate(res.get('payloads', [])):
                print(f"\nPayload {i+1} (Type: {p['type']}, Label: {p['label']}):")
                # Save to disk
                output_path = os.path.join(persist_dir, f"react_payload_{i+1}.json")
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(p['data'], f, indent=2, ensure_ascii=False)
                print(f"Saved payload details to {output_path}")
                print(json.dumps(p['data'], indent=2, ensure_ascii=False)[:1500])
                print("-" * 50)
    else:
        print("Search returned nothing.")
        
    ws.close()

if __name__ == "__main__":
    main()
