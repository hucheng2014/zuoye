import json
import urllib.request
import time
import sys
from websocket import create_connection

def main():
    ws_url = "ws://127.0.0.1:9233/devtools/page/47A7A5FE9C866D76A69366F322A9B073"
    try:
        ws = create_connection(ws_url, timeout=15)
    except Exception as e:
        print("Failed to connect:", e)
        sys.exit(1)
        
    ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
    ws.recv()
    ws.send(json.dumps({"id": 2, "method": "Runtime.enable"}))
    ws.recv()
    
    # 1. Navigate to bug report page
    print("Navigating to bug report page...")
    ws.send(json.dumps({
        "id": 10,
        "method": "Page.navigate",
        "params": {"url": "https://globalquery.oneforma.com/bug_report_page.php"}
    }))
    ws.recv()
    
    # Wait for page to load
    time.sleep(4)
    
    # 2. Extract form elements (Categories list)
    extract_js = """
    (() => {
        let categorySelect = document.querySelector('select[name="category_id"]');
        let categories = [];
        if (categorySelect) {
            Array.from(categorySelect.options).forEach(opt => {
                categories.push({
                    value: opt.value,
                    text: opt.text
                });
            });
        }
        
        let inputs = [];
        document.querySelectorAll('input, textarea, select').forEach(el => {
            if (el.name) {
                inputs.push({
                    tagName: el.tagName,
                    name: el.name,
                    id: el.id,
                    type: el.type || ''
                });
            }
        });
        
        return JSON.stringify({
            categories: categories,
            inputs: inputs,
            url: location.href
        });
    })()
    """
    
    ws.send(json.dumps({"id": 100, "method": "Runtime.evaluate", "params": {"expression": extract_js, "returnByValue": True}}))
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == 100:
            res_val = data.get("result", {}).get("result", {}).get("value")
            if res_val:
                res = json.loads(res_val)
                print("\n=== CURRENT URL ===")
                print(res['url'])
                print("\n=== CATEGORIES FOUND ===")
                for c in res['categories']:
                    print(f"Value: {c['value']} -> Label: {repr(c['text'])}")
                print("\n=== FORM INPUTS ===")
                for i in res['inputs']:
                    print(f"Tag: {i['tagName']}, Name: {i['name']}, ID: {i['id']}, Type: {i['type']}")
            else:
                print("Failed to evaluate form details.")
            break
            
    ws.close()

if __name__ == "__main__":
    main()
