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
    ws = create_connection(ws_url, timeout=20)
    
    ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
    ws.recv()
    
    screenshot_payload = {
        "id": 2,
        "method": "Page.captureScreenshot",
        "params": {
            "format": "png"
        }
    }
    ws.send(json.dumps(screenshot_payload))
    img_data = None
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == 2:
            img_data = data.get("result", {}).get("data")
            break
            
    persist_dir = "/Users/xaa/zuoye/oneform/kuokka add"
    if img_data:
        screenshot_path = os.path.join(persist_dir, "current_view.png")
        with open(screenshot_path, "wb") as f:
            f.write(base64.b64decode(img_data))
        print(f"Screenshot successfully saved to {screenshot_path}")
    else:
        print("Failed to capture screenshot.")
    ws.close()

if __name__ == "__main__":
    main()
