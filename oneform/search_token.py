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
        let results = {};
        
        // Search window properties
        for (let k in window) {
            let l = k.toLowerCase();
            if (l.includes('keycloak') || l.includes('auth') || l.includes('token') || l.includes('jwt')) {
                results[k] = String(window[k]).substring(0, 500);
                if (window[k] && typeof window[k] === 'object') {
                    // Try to extract nested token properties
                    try {
                        results[k + "_keys"] = Object.keys(window[k]);
                        if (window[k].token) results[k + "_token"] = window[k].token.substring(0, 100);
                        if (window[k].idToken) results[k + "_idToken"] = window[k].idToken.substring(0, 100);
                    } catch(e) {}
                }
            }
        }
        
        // Search in iframes as well
        document.querySelectorAll('iframe').forEach((iframe, idx) => {
            try {
                let win = iframe.contentWindow;
                for (let k in win) {
                    let l = k.toLowerCase();
                    if (l.includes('keycloak') || l.includes('auth') || l.includes('token') || l.includes('jwt') || l.includes('task') || l.includes('props')) {
                        results["iframe_" + idx + "_" + k] = String(win[k]).substring(0, 500);
                        if (win[k] && typeof win[k] === 'object') {
                            try {
                                results["iframe_" + idx + "_" + k + "_keys"] = Object.keys(win[k]);
                                if (win[k].token) results["iframe_" + idx + "_" + k + "_token"] = win[k].token.substring(0, 100);
                            } catch(e) {}
                        }
                    }
                }
            } catch(e) {
                results["iframe_" + idx + "_error"] = e.message;
            }
        });
        
        return JSON.stringify(results);
    })()
    """
    
    res_str = evaluate(search_js)
    if res_str:
        res = json.loads(res_str)
        print(json.dumps(res, indent=2))
    else:
        print("Search returned nothing.")
        
    ws.close()

if __name__ == "__main__":
    main()
