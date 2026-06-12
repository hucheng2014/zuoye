import json
import urllib.request
import time
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
    ws = create_connection(ws_url, timeout=20)
    
    ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
    ws.recv()
    ws.send(json.dumps({"id": 2, "method": "Page.enable"}))
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
                
    # JS code to focus iframe and simulate Spacebar key down/up
    play_js = """
    (() => {
        let iframe = document.querySelector('iframe');
        if (!iframe) return "Iframe not found";
        
        let win = iframe.contentWindow;
        let doc = iframe.contentDocument || win.document;
        
        // Find play button in DOM first
        let buttons = Array.from(doc.querySelectorAll('button, svg, path, div'));
        // Starshot players usually have a play icon (triangle) or test matching
        let playBtn = doc.querySelector('.play') || doc.querySelector('[class*="play"]') || doc.querySelector('[id*="play"]');
        
        if (playBtn) {
            playBtn.click();
            return "Clicked play button element";
        }
        
        // Otherwise, focus the window and send Spacebar
        win.focus();
        doc.body.focus();
        
        let event = new KeyboardEvent('keydown', {
            key: ' ',
            code: 'Space',
            keyCode: 32,
            which: 32,
            bubbles: true,
            cancelable: true
        });
        doc.body.dispatchEvent(event);
        
        let eventUp = new KeyboardEvent('keyup', {
            key: ' ',
            code: 'Space',
            keyCode: 32,
            which: 32,
            bubbles: true,
            cancelable: true
        });
        doc.body.dispatchEvent(eventUp);
        
        return "Dispatched Spacebar key events";
    })()
    """
    
    # 1. Capture resources before play
    res_before = json.loads(evaluate("JSON.stringify(performance.getEntries().map(e => e.name))"))
    
    print("Triggering audio play...")
    play_res = evaluate(play_js)
    print("Play trigger result:", play_res)
    
    # Wait for audio download
    print("Waiting 5 seconds for audio download to trigger...")
    time.sleep(5)
    
    # 2. Capture resources after play
    res_after = json.loads(evaluate("JSON.stringify(performance.getEntries().map(e => e.name))"))
    
    new_resources = [r for r in res_after if r not in res_before]
    print(f"\nFound {len(new_resources)} new resources loaded after play:")
    for r in new_resources:
        print(f"- {r}")
        
    ws.close()

if __name__ == "__main__":
    main()
