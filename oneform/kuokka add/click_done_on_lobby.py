import json
import urllib.request
import time
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
    ws.send(json.dumps({"id": 2, "method": "Network.enable"}))
    ws.recv()
    
    # Click Done button on the lobby page
    # Since Done button has text 'Done' or id 'starshot_submit_button'
    click_js = """
    (() => {
        let btn = document.getElementById('starshot_submit_button') || 
                  Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Done');
        if (btn) {
            btn.click();
            return "Clicked Done button";
        }
        return "Done button not found";
    })()
    """
    print("Clicking Done on the lobby page...")
    ws.send(json.dumps({"id": 100, "method": "Runtime.evaluate", "params": {"expression": click_js, "returnByValue": True}}))
    
    # We will log any network requests or responses for 5 seconds to see what is sent
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
                print(f"Request: {request.get('method')} {request.get('url')}")
            elif data.get("id") == 100:
                print("Click Evaluation Result:", data.get("result", {}).get("result", {}).get("value"))
        except Exception:
            continue
            
    # Get the final page URL and text
    ws.send(json.dumps({"id": 200, "method": "Runtime.evaluate", "params": {"expression": "location.href", "returnByValue": True}}))
    while True:
        try:
            raw = ws.recv()
            data = json.loads(raw)
            if data.get("id") == 200:
                print("Final URL after click:", data.get("result", {}).get("result", {}).get("value"))
                break
        except Exception: pass
        
    ws.close()

if __name__ == "__main__":
    main()
