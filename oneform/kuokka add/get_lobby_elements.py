import json
import urllib.request
import sys
from websocket import create_connection

def main():
    # Connect to the lobby tab
    ws_url = "ws://127.0.0.1:9233/devtools/page/325AA314492EFDE9DF9AEBD59C54F3E7"
    try:
        ws = create_connection(ws_url, timeout=10)
    except Exception as e:
        print("Failed to connect:", e)
        sys.exit(1)
        
    ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
    try:
        ws.recv()
    except Exception: pass
    
    js = """
    (() => {
        let el_info = [];
        document.querySelectorAll('button, a, [role=\"button\"]').forEach((el, idx) => {
            el_info.push({
                index: idx,
                tag: el.tagName,
                text: (el.innerText || '').trim(),
                aria: el.getAttribute('aria-label') || '',
                id: el.id || '',
                className: el.className || ''
            });
        });
        return JSON.stringify({
            body: document.body.innerText,
            elements: el_info
        });
    })()
    """
    ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
    
    response = None
    try:
        # Loop to consume any async events until we get the response for id 2
        for _ in range(50):
            raw = ws.recv()
            data = json.loads(raw)
            if data.get("id") == 2:
                response = data
                break
    except Exception as e:
        print("Error receiving data:", e)
        
    ws.close()
    
    if response:
        val_str = response.get("result", {}).get("result", {}).get("value")
        if val_str:
            val = json.loads(val_str)
            print("\n=== LOBBY TEXT ===")
            print(val['body'])
            print("\n=== INTERACTIVE ELEMENTS ===")
            for el in val['elements']:
                print(f"- {el['tag']} id: {repr(el['id'])}, text: {repr(el['text'])}, aria: {repr(el['aria'])}, class: {repr(el['className'])}")
        else:
            print("Response value was empty.")
    else:
        print("Did not receive response.")

if __name__ == "__main__":
    main()
