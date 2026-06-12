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
                
    # JS code to deep extract the assets object
    assets_js = """
    (() => {
        let iframe = document.querySelector('iframe');
        if (!iframe) return "Error: No iframe found";
        
        try {
            let doc = iframe.contentDocument || iframe.contentWindow.document;
            let root = doc.querySelector('#root') || doc.body;
            let keys = Object.keys(root);
            let containerKey = keys.find(k => k.startsWith('__reactContainer') || k.startsWith('__reactFiber'));
            if (!containerKey) return "Error: No React Container found";
            
            let fiber = root[containerKey];
            
            // Find task object
            let taskObj = null;
            let child = fiber;
            for (let i = 0; i < 10; i++) {
                if (!child) break;
                if (child.memoizedProps && child.memoizedProps.task) {
                    taskObj = child.memoizedProps.task;
                    break;
                }
                child = child.child;
            }
            
            if (!taskObj) return "Error: task object not found in tree";
            
            return JSON.stringify({
                assets: taskObj.assets,
                pluginConfig_questions: taskObj.pluginConfig ? taskObj.pluginConfig.questions : null,
                preannotations: taskObj.preannotations || null
            });
        } catch(e) {
            return "Error: " + e.message;
        }
    })()
    """
    
    res_str = evaluate(assets_js)
    if res_str:
        if res_str.startswith("Error"):
            print(res_str)
        else:
            res = json.loads(res_str)
            print("\n=== TASK ASSETS ===")
            print(json.dumps(res.get('assets'), indent=2, ensure_ascii=False))
            print("\n=== PREANNOTATIONS ===")
            print(json.dumps(res.get('preannotations'), indent=2, ensure_ascii=False))
            print("\n=== QUESTIONS SCHEMA ===")
            print(json.dumps(res.get('pluginConfig_questions'), indent=2, ensure_ascii=False))
    else:
        print("Search returned nothing.")
        
    ws.close()

if __name__ == "__main__":
    main()
