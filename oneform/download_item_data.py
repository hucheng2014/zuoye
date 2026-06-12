import json
import urllib.request
import base64
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
                
    url = "https://assets-public.scilliance.com/89ff40213b40404fa60ada2ed2b96164/ds/items/d88e9605-4b22-457a-be27-6fd4286ee8f4/b86af0f1-2070-4464-894b-59bd33b5e625/303d3614-2f9b-40f8-9333-7970dc94f24b"
    
    print(f"Fetching item data from {url}...")
    fetch_js = """
    (async () => {
        try {
            let r = await fetch("URL_PLACEHOLDER");
            let contentType = r.headers.get("content-type") || "";
            if (contentType.includes("json")) {
                let data = await r.json();
                return JSON.stringify({ type: "json", data: data });
            } else {
                let buffer = await r.arrayBuffer();
                let binary = '';
                let bytes = new Uint8Array(buffer);
                let len = bytes.byteLength;
                for (let i = 0; i < len; i++) {
                    binary += String.fromCharCode(bytes[i]);
                }
                return JSON.stringify({ type: "binary", contentType: contentType, data: window.btoa(binary) });
            }
        } catch(e) {
            return JSON.stringify({ type: "error", error: e.message });
        }
    })()
    """.replace("URL_PLACEHOLDER", url)
    
    result_str = evaluate(fetch_js)
    if result_str:
        result = json.loads(result_str)
        t = result.get("type")
        persist_dir = "/Users/xaa/zuoye/oneform/kuokka add"
        
        if t == "json":
            output_path = os.path.join(persist_dir, "task_item_data.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result.get("data"), f, indent=2, ensure_ascii=False)
            print(f"Saved JSON data to {output_path}")
            print(json.dumps(result.get("data"), indent=2, ensure_ascii=False)[:1000])
        elif t == "binary":
            ct = result.get("contentType", "")
            ext = ".wav" if "wav" in ct.lower() or "audio" in ct.lower() else ".bin"
            output_path = os.path.join(persist_dir, "task_item_data" + ext)
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(result.get("data")))
            print(f"Saved binary data ({ct}) to {output_path}")
        else:
            print("Error fetching data:", result.get("error"))
    else:
        print("Fetch script returned empty.")
        
    ws.close()

if __name__ == "__main__":
    main()
