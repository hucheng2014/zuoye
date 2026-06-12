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
                
    # 1. Click "Start" button on the modal popup
    print("Clicking 'Start' button...")
    click_js = """
    (() => {
        let btn = document.getElementById('help-modal-close');
        if (btn) {
            btn.click();
            return "Clicked button#help-modal-close";
        }
        btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Start');
        if (btn) {
            btn.click();
            return "Clicked Start button by text";
        }
        return "Start button not found";
    })()
    """
    click_res = evaluate(click_js)
    print("Start Click Result:", click_res)
    
    # 2. Wait for the task page to load (usually loads within 3-5 seconds)
    print("Waiting for task to load...")
    time.sleep(5)
    
    # 3. Take a screenshot of the loaded task
    print("Capturing screenshot of the loaded task...")
    screenshot_payload = {
        "id": 200,
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
        if data.get("id") == 200:
            img_data = data.get("result", {}).get("data")
            break
            
    persist_dir = "/Users/xaa/zuoye/oneform/kuokka add"
    if img_data:
        screenshot_path = os.path.join(persist_dir, "task_loaded.png")
        with open(screenshot_path, "wb") as f:
            f.write(base64.b64decode(img_data))
        print(f"Screenshot saved to {screenshot_path}")
    else:
        print("Failed to capture screenshot.")
        
    # 4. Extract task details and iframe contents
    print("Extracting task details...")
    task_details_js = """
    (() => {
        let results = {};
        results.url = location.href;
        results.title = document.title;
        results.body_text = document.body.innerText.substring(0, 3000);
        
        // Find iframes
        let iframes = [];
        document.querySelectorAll("iframe").forEach((iframe, i) => {
            let innerText = "";
            let innerHTML = "";
            try {
                if (iframe.contentDocument) {
                    innerText = iframe.contentDocument.body.innerText;
                    innerHTML = iframe.contentDocument.body.innerHTML;
                }
            } catch(e) {
                innerText = "CORS Error: " + e.message;
            }
            iframes.push({
                index: i,
                src: iframe.src,
                text: innerText.substring(0, 3000),
                html: innerHTML.substring(0, 5000)
            });
        });
        results.iframes = iframes;
        
        return JSON.stringify(results);
    })()
    """
    
    task_info_str = evaluate(task_details_js)
    task_info = json.loads(task_info_str) if task_info_str else {}
    
    # Save the task state locally for persistence
    state_path = os.path.join(persist_dir, "task_state.json")
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(task_info, f, indent=2, ensure_ascii=False)
    print(f"Task state details saved to {state_path}")
    
    # 5. Output summary of the loaded page
    print("\n=== LOADED TASK SUMMARY ===")
    print("URL:", task_info.get('url'))
    print("Body text snippet:\n", task_info.get('body_text', '')[:1000])
    for iframe in task_info.get('iframes', []):
        print(f"\n--- Iframe {iframe['index']} (src: {iframe['src']}) ---")
        print("Text snippet:\n", iframe['text'][:1500])
        
    ws.close()

if __name__ == "__main__":
    main()
