import json
import urllib.request
import sys
from websocket import create_connection

def main():
    ws_url = "ws://127.0.0.1:9233/devtools/page/47A7A5FE9C866D76A69366F322A9B073"
    try:
        ws = create_connection(ws_url, timeout=15)
    except Exception as e:
        print("Failed to connect:", e)
        sys.exit(1)
        
    ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
    ws.recv()
    
    inspect_labels_js = """
    (() => {
        let fields = [];
        let rows = document.querySelectorAll('form tr');
        rows.forEach((tr, idx) => {
            let tds = tr.querySelectorAll('td');
            if (tds.length >= 1) {
                let labelText = tds[0].innerText.trim();
                let inputs = [];
                tr.querySelectorAll('input, textarea, select').forEach(el => {
                    if (el.name) {
                        inputs.push({
                            tagName: el.tagName,
                            name: el.name,
                            type: el.type || '',
                            id: el.id || ''
                        });
                    }
                });
                if (labelText || inputs.length > 0) {
                    fields.push({
                        label: labelText,
                        inputs: inputs
                    });
                }
            }
        });
        return JSON.stringify(fields);
    })()
    """
    
    ws.send(json.dumps({"id": 100, "method": "Runtime.evaluate", "params": {"expression": inspect_labels_js, "returnByValue": True}}))
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == 100:
            val_str = data.get("result", {}).get("result", {}).get("value")
            if val_str:
                val = json.loads(val_str)
                print("\n=== FORM LABELS AND FIELDS ===")
                for idx, f in enumerate(val):
                    print(f"\nRow {idx+1}: {repr(f['label'])}")
                    for inp in f['inputs']:
                        print(f"  -> Input: Name={inp['name']}, Tag={inp['tagName']}, Type={inp['type']}")
            else:
                print("Failed to get form labels.")
            break
            
    ws.close()

if __name__ == "__main__":
    main()
