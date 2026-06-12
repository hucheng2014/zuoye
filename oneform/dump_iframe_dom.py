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
                
    search_js = """
    (() => {
        let results = [];
        let iframe = document.querySelector('iframe');
        if (!iframe) return JSON.stringify({ error: "No iframe found" });
        
        try {
            let doc = iframe.contentDocument || iframe.contentWindow.document;
            doc.querySelectorAll('*').forEach(el => {
                let attrs = {};
                let has_attr = false;
                for (let i = 0; i < el.attributes.length; i++) {
                    let attr = el.attributes[i];
                    if (['src', 'href', 'url', 'data-src', 'data-url'].includes(attr.name.toLowerCase()) || attr.value.includes('http') || attr.value.includes('assets-public')) {
                        attrs[attr.name] = attr.value;
                        has_attr = true;
                    }
                }
                if (has_attr) {
                    results.push({
                        tag: el.tagName,
                        id: el.id,
                        className: el.className,
                        attributes: attrs
                    });
                }
            });
            return JSON.stringify(results);
        } catch(e) {
            return JSON.stringify({ error: e.message });
        }
    })()
    """
    
    res_str = evaluate(search_js)
    if res_str:
        res = json.loads(res_str)
        if isinstance(res, dict) and "error" in res:
            print("Error:", res["error"])
        else:
            print(f"Found {len(res)} elements with URL/src attributes:")
            for item in res:
                print(f"- [{item['tag']}] ID: {item['id']}, Class: {item['className']}")
                print("  Attrs:", item['attributes'])
    else:
        print("Search returned nothing.")
        
    ws.close()

if __name__ == "__main__":
    main()
