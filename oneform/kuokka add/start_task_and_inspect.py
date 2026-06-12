import json
import urllib.request
import base64
import time
import sys
import os
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
        print("Error: Could not connect to CDP.")
        sys.exit(1)
        
    page = [p for p in pages if p.get('type') == 'page' and "Annotation Tool" in p.get('title', '')][0]
    ws_url = page['webSocketDebuggerUrl']
    ws = create_connection(ws_url, timeout=30)
    
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

    # 1. Click "Start" if in lobby
    print("Checking if we need to click Start...")
    click_js = """
    (() => {
        let btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Start');
        if (btn) {
            btn.click();
            return "Clicked Start button";
        }
        return "Start button not found or already in workspace";
    })()
    """
    res = evaluate(click_js)
    print("Start status:", res)
    
    print("Waiting 5 seconds for workspace to load...")
    time.sleep(5)
    
    # 2. Capture screenshot of the workspace
    print("Capturing workspace screenshot...")
    screenshot_payload = {
        "id": 200,
        "method": "Page.captureScreenshot",
        "params": {"format": "png"}
    }
    ws.send(json.dumps(screenshot_payload))
    img_data = None
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == 200:
            img_data = data.get("result", {}).get("data")
            break
            
    persist_dir = "/Users/xaa/zuoye/oneform/kuokka add"
    if img_data:
        screenshot_path = os.path.join(persist_dir, "workspace_loaded.png")
        with open(screenshot_path, "wb") as f:
            f.write(base64.b64decode(img_data))
        print(f"Saved screenshot to {screenshot_path}")
        # Copy to artifacts directory
        os.system(f'cp "{screenshot_path}" "/Users/xaa/.gemini/antigravity-cli/brain/7f207531-9de7-4f95-9c38-e583af332566/workspace_loaded.png"')
    
    # 3. Extract text details and interactive elements (especially Skip button)
    print("Extracting workspace DOM details...")
    dom_js = """
    (() => {
        let result = {};
        result.body_text = document.body.innerText;
        
        // Find buttons
        let buttons = [];
        document.querySelectorAll('button').forEach(btn => {
            buttons.push({
                text: btn.innerText,
                id: btn.id,
                className: btn.className,
                disabled: btn.disabled
            });
        });
        result.buttons = buttons;
        
        // Check inside iframe
        let iframe = document.querySelector('iframe');
        if (iframe) {
            try {
                let doc = iframe.contentDocument || iframe.contentWindow.document;
                result.iframe_body_text = doc.body.innerText;
                let iframe_buttons = [];
                doc.querySelectorAll('button').forEach(btn => {
                    iframe_buttons.push({
                        text: btn.innerText,
                        id: btn.id,
                        className: btn.className,
                        disabled: btn.disabled
                    });
                });
                result.iframe_buttons = iframe_buttons;
            } catch(e) {
                result.iframe_error = e.message;
            }
        }
        return JSON.stringify(result);
    })()
    """
    dom_str = evaluate(dom_js)
    if dom_str:
        dom_data = json.loads(dom_str)
        output_path = os.path.join(persist_dir, "workspace_dom.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dom_data, f, indent=2, ensure_ascii=False)
        print(f"Saved workspace DOM info to {output_path}")
        
        # Let's inspect buttons specifically
        print("\n=== BUTTONS FOUND IN MAIN WINDOW ===")
        for b in dom_data.get("buttons", []):
            print(f"- Button text: {repr(b['text'])}, id: {b['id']}, class: {b['className']}, disabled: {b['disabled']}")
            
        if "iframe_buttons" in dom_data:
            print("\n=== BUTTONS FOUND IN IFRAME ===")
            for b in dom_data.get("iframe_buttons", []):
                print(f"- Button text: {repr(b['text'])}, id: {b['id']}, class: {b['className']}, disabled: {b['disabled']}")
        else:
            print("\nNo iframe buttons or iframe CORS error:", dom_data.get("iframe_error"))
            
    ws.close()

if __name__ == "__main__":
    main()
