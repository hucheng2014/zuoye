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
    
    # JS to select 'Expertise Mismatch' and click 'Submit'
    skip_js = """
    (() => {
        // 1. Find and click the radio option for Expertise Mismatch
        let optionText = 'Expertise Mismatch';
        let optionEl = Array.from(document.querySelectorAll('label, span, div, p')).find(el => {
            return el.innerText && el.innerText.trim() === optionText;
        });
        
        if (!optionEl) {
            return "Option element not found";
        }
        
        // Click the option label/wrapper
        optionEl.click();
        
        // Try to click any checkbox/radio input associated with it
        let input = optionEl.querySelector('input') || 
                    (optionEl.parentElement && optionEl.parentElement.querySelector('input'));
        if (input) {
            input.click();
        }
        
        // 2. Find and click the 'Submit' button
        let submitBtn = Array.from(document.querySelectorAll('button, div, span')).find(b => {
            return b.innerText && b.innerText.trim() === 'Submit';
        });
        
        if (!submitBtn) {
            return "Expertise Mismatch selected, but Submit button not found";
        }
        
        submitBtn.click();
        return "Selected Expertise Mismatch and clicked Submit";
    })()
    """
    
    print("Executing skip action...")
    ws.send(json.dumps({"id": 100, "method": "Runtime.evaluate", "params": {"expression": skip_js, "returnByValue": True}}))
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == 100:
            print("Evaluation Result:", data.get("result", {}).get("result", {}).get("value"))
            break
            
    # Wait 3 seconds for backend to process skip and reload lobby
    print("Waiting 3 seconds for skip to process...")
    time.sleep(3)
    
    # Get final page URL and body text
    ws.send(json.dumps({"id": 200, "method": "Runtime.evaluate", "params": {"expression": "document.body.innerText", "returnByValue": True}}))
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == 200:
            print("\n=== PAGE TEXT AFTER SUBMITTING SKIP ===")
            print(data.get("result", {}).get("result", {}).get("value"))
            break
            
    ws.close()

if __name__ == "__main__":
    main()
