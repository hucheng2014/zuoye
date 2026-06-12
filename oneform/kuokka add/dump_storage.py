import json
import urllib.request
import sys
from websocket import create_connection

def main():
    ports = [9233, 9232]
    pages = None
    for port in ports:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/json/list")
            with urllib.request.urlopen(req, timeout=5) as resp:
                pages = json.loads(resp.read())
                break
        except Exception: pass
    if not pages:
        print("Error connecting")
        sys.exit(1)
    page = [p for p in pages if p.get('type') == 'page' and "Annotation Tool" in p.get('title', '')][0]
    ws = create_connection(page['webSocketDebuggerUrl'], timeout=15)
    ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
    ws.recv()
    
    js = """
    (() => {
        return JSON.stringify({
            main_localStorage: Object.keys(localStorage).reduce((acc, k) => ({...acc, [k]: localStorage.getItem(k).substring(0, 150)}), {}),
            main_sessionStorage: Object.keys(sessionStorage).reduce((acc, k) => ({...acc, [k]: sessionStorage.getItem(k).substring(0, 150)}), {}),
            main_cookies: document.cookie,
            iframe_localStorage: (() => {
                try {
                    let iframe = document.querySelector('iframe');
                    let win = iframe.contentWindow;
                    return Object.keys(win.localStorage).reduce((acc, k) => ({...acc, [k]: win.localStorage.getItem(k).substring(0, 150)}), {});
                } catch(e) { return e.message; }
            })(),
            iframe_sessionStorage: (() => {
                try {
                    let iframe = document.querySelector('iframe');
                    let win = iframe.contentWindow;
                    return Object.keys(win.sessionStorage).reduce((acc, k) => ({...acc, [k]: win.sessionStorage.getItem(k).substring(0, 150)}), {});
                } catch(e) { return e.message; }
            })(),
            iframe_cookies: (() => {
                try {
                    let iframe = document.querySelector('iframe');
                    return iframe.contentDocument.cookie;
                } catch(e) { return e.message; }
            })()
        });
    })()
    """
    ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == 2:
            break
    val = data.get("result", {}).get("result", {}).get("value")
    if val:
        print(json.dumps(json.loads(val), indent=2))
    else:
        print("No storage found")
    ws.close()

if __name__ == "__main__":
    main()
