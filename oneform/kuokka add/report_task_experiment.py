import json
import urllib.request
import time
import base64
import os
import sys
from websocket import create_connection

def main():
    ws_url = "ws://127.0.0.1:9233/devtools/page/325AA314492EFDE9DF9AEBD59C54F3E7"
    try:
        ws = create_connection(ws_url, timeout=15)
    except Exception as e:
        print("Failed to connect:", e)
        sys.exit(1)
        
    ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
    ws.recv()
    ws.send(json.dumps({"id": 2, "method": "Page.enable"}))
    ws.recv()
    ws.send(json.dumps({"id": 3, "method": "Network.enable"}))
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
                return data.get("result", {}).get("result", {}).get("value")

    # 1. Click Start to enter workspace
    print("Clicking Start to enter workspace...")
    click_start_js = """
    (() => {
        // First restore hidden overlays if they were hidden in this session
        document.querySelectorAll('div').forEach(el => {
            if (el.style.display === 'none') el.style.display = '';
        });
        let btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Start');
        if (btn) {
            btn.click();
            return "Clicked Start";
        }
        return "Start button not found";
    })()
    """
    print("Start result:", evaluate(click_start_js))
    time.sleep(5)
    
    # 2. Click Report a Problem
    print("Clicking Report a Problem button...")
    click_report_menu_js = """
    (() => {
        let btn = Array.from(document.querySelectorAll('button')).find(b => b.getAttribute('aria-label') === 'Report a Problem');
        if (btn) {
            btn.click();
            return "Clicked Report menu";
        }
        return "Report menu button not found";
    })()
    """
    print("Report menu result:", evaluate(click_report_menu_js))
    time.sleep(2)
    
    # 3. Monitor network and click Report Task inside the modal
    # We will search for button with text "Report Task"
    click_report_task_js = """
    (() => {
        let btn = Array.from(document.querySelectorAll('button, a, div, span')).find(b => b.innerText && b.innerText.trim() === 'Report Task');
        if (btn) {
            btn.click();
            return "Clicked Report Task Button";
        }
        return "Report Task Button not found";
    })()
    """
    print("Clicking Report Task...")
    ws.send(json.dumps({"id": 101, "method": "Runtime.evaluate", "params": {"expression": click_report_task_js, "returnByValue": True}}))
    
    # Listen to network requests for 5 seconds
    start_time = time.time()
    while time.time() - start_time < 5:
        try:
            ws.settimeout(0.5)
            raw = ws.recv()
            data = json.loads(raw)
            method = data.get("method")
            if method == "Network.requestWillBeSent":
                params = data.get("params", {})
                request = params.get("request", {})
                print(f"Network Request: {request.get('method')} {request.get('url')}")
            elif data.get("id") == 101:
                print("Report Task click result:", data.get("result", {}).get("result", {}).get("value"))
        except Exception:
            continue
            
    time.sleep(2)
    
    # Capture screenshot to see the report page state
    ws.send(json.dumps({"id": 300, "method": "Page.captureScreenshot", "params": {"format": "png"}}))
    img_data = None
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == 300:
            img_data = data.get("result", {}).get("data")
            break
            
    persist_dir = "/Users/xaa/zuoye/oneform/kuokka add"
    if img_data:
        screenshot_path = os.path.join(persist_dir, "report_page.png")
        with open(screenshot_path, "wb") as f:
            f.write(base64.b64decode(img_data))
        print("Saved screenshot of report page to:", screenshot_path)
        os.system(f'cp "{screenshot_path}" "/Users/xaa/.gemini/antigravity-cli/brain/7f207531-9de7-4f95-9c38-e583af332566/report_page.png"')
        
    ws.close()

if __name__ == "__main__":
    main()
