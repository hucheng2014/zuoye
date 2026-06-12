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

    # JS code to find and serialize the task object with deep serialization
    js_extract = """
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
            let visited = new Set();
            let foundTask = null;
            let foundIngestedTasks = null;
            
            function traverseFiber(node) {
                if (!node || visited.has(node) || foundTask) return;
                visited.add(node);
                
                let props = node.memoizedProps;
                let state = node.memoizedState;
                
                if (props && props.task) {
                    foundTask = props.task;
                }
                if (state && state.task) {
                    foundTask = state.task;
                }
                if (state && state.ingestedTasks) {
                    foundIngestedTasks = state.ingestedTasks;
                }
                
                if (node.child) traverseFiber(node.child);
                if (node.sibling) traverseFiber(node.sibling);
            }
            
            traverseFiber(fiber);
            
            if (!foundTask) return JSON.stringify({ error: "Task object not found in fiber tree" });
            
            // Custom deep serializer to serialize the task object
            function deepSerialize(o, depth = 0) {
                if (depth > 12) return "[Depth Limit]";
                if (o === null || o === undefined) return o;
                if (typeof o !== 'object') return o;
                
                if (Array.isArray(o)) {
                    return o.map(x => deepSerialize(x, depth + 1));
                }
                
                let res = {};
                for (let k in o) {
                    // avoid circular/internal fields
                    if (k.startsWith('_') || k === 'theme') continue;
                    let val = o[k];
                    let t = typeof val;
                    if (t === 'function') {
                        res[k] = "[Function]";
                    } else {
                        res[k] = deepSerialize(val, depth + 1);
                    }
                }
                return res;
            }
            
            let result = {
                task: deepSerialize(foundTask),
                ingestedTasks: foundIngestedTasks ? deepSerialize(foundIngestedTasks) : null
            };
            
            return JSON.stringify(result);
        } catch(e) {
            return JSON.stringify({ error: e.message });
        }
    })()
    """
    
    res_str = evaluate(js_extract)
    if res_str:
        res = json.loads(res_str)
        if "error" in res:
            print("Error:", res["error"])
        else:
            persist_dir = "/Users/xaa/zuoye/oneform/kuokka add"
            output_path = os.path.join(persist_dir, "extracted_task_details.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2, ensure_ascii=False)
            print(f"Successfully saved deep task details to {output_path}")
            
            # Print a quick summary of the assets and questions
            task = res.get("task", {})
            assets = task.get("assets", {})
            print("\n=== AUDIO ASSETS ===")
            print(json.dumps(assets.get("audio"), indent=2))
            
            print("\n=== QUESTIONS ===")
            questions = task.get("pluginConfig", {}).get("questions", [])
            print(f"Number of questions: {len(questions)}")
            for q in questions:
                print(f"- Question Type: {q.get('type')}, Label: {q.get('label')}")
    else:
        print("Evaluation returned nothing.")
        
    ws.close()

if __name__ == "__main__":
    main()
