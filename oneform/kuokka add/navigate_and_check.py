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
    port = None
    for p_port in ports:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{p_port}/json/list")
            with urllib.request.urlopen(req, timeout=5) as resp:
                pages = json.loads(resp.read())
                port = p_port
                break
        except Exception: pass
    if not pages:
        print("Error: Could not connect to CDP.")
        sys.exit(1)
        
    # We find any active page to send Target.createTarget
    page = pages[0]
    ws_url = page['webSocketDebuggerUrl']
    print(f"Connecting to existing tab to spawn a new target: {page['title']} ({ws_url})")
    
    ws = create_connection(ws_url, timeout=15)
    
    # Create new target
    target_url = "https://starshot.scilliance.com/?broker=true"
    payload = {
        "id": 10,
        "method": "Target.createTarget",
        "params": {
            "url": target_url
        }
    }
    ws.send(json.dumps(payload))
    target_id = None
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == 10:
            target_id = data.get("result", {}).get("targetId")
            break
            
    ws.close()
    
    if not target_id:
        print("Failed to create new target.")
        sys.exit(1)
        
    print(f"Successfully created target: {target_id}")
    
    # Connect to the new target's WebSocket
    new_ws_url = f"ws://127.0.0.1:{port}/devtools/page/{target_id}"
    print(f"Connecting to new tab: {new_ws_url}")
    ws_new = create_connection(new_ws_url, timeout=30)
    
    ws_new.send(json.dumps({"id": 1, "method": "Page.enable"}))
    ws_new.recv()
    ws_new.send(json.dumps({"id": 2, "method": "Runtime.enable"}))
    ws_new.recv()
    
    print("Waiting 5 seconds for lobby to load...")
    time.sleep(5)
    
    # Capture screenshot
    screenshot_payload = {
        "id": 200,
        "method": "Page.captureScreenshot",
        "params": {"format": "png"}
    }
    ws_new.send(json.dumps(screenshot_payload))
    img_data = None
    while True:
        raw = ws_new.recv()
        data = json.loads(raw)
        if data.get("id") == 200:
            img_data = data.get("result", {}).get("data")
            break
            
    persist_dir = "/Users/xaa/zuoye/oneform/kuokka add"
    if img_data:
        screenshot_path = os.path.join(persist_dir, "lobby_loaded.png")
        with open(screenshot_path, "wb") as f:
            f.write(base64.b64decode(img_data))
        print(f"Saved lobby screenshot to {screenshot_path}")
        os.system(f'cp "{screenshot_path}" "/Users/xaa/.gemini/antigravity-cli/brain/7f207531-9de7-4f95-9c38-e583af332566/lobby_loaded.png"')
        
    # Extract DOM details of the lobby page
    js = """
    (() => {
        let elements = [];
        document.querySelectorAll('button, a, [role=\"button\"]').forEach((el, idx) => {
            let text = el.innerText || '';
            let aria = el.getAttribute('aria-label') || '';
            let id = el.id || '';
            let tag = el.tagName;
            if (text || aria || id) {
                elements.push({ index: idx, tag, id, text: text.trim(), aria });
            }
        });
        return JSON.stringify({
            body: document.body.innerText,
            elements: elements
        });
    })()
    """
    ws_new.send(json.dumps({"id": 100, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
    while True:
        raw = ws_new.recv()
        data = json.loads(raw)
        if data.get("id") == 100:
            val = json.loads(data['result']['result']['value'])
            print("\n=== LOBBY TEXT ===")
            print(repr(val['body']))
            print("\n=== LOBBY BUTTONS ===")
            for el in val['elements']:
                print(f"- {el['tag']} id: {repr(el['id'])}, text: {repr(el['text'])}, aria: {repr(el['aria'])}")
            break
            
    ws_new.close()

if __name__ == "__main__":
    main()
