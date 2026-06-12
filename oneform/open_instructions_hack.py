import json
import urllib.request
import time
import sys
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
    ws = create_connection(ws_url, timeout=15)
    
    ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
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
                    print("Error running JS:", res["exceptionDetails"])
                    return None
                return res.get("result", {}).get("value")
                
    # JS code to temporarily hide modal, click instructions, get text, and restore modal
    hack_js = """
    (() => {
        let results = {};
        
        // 1. Find modal dialog and overlays
        let modal = document.querySelector('[role="dialog"]');
        let overlays = [];
        document.querySelectorAll('div').forEach(div => {
            let style = window.getComputedStyle(div);
            if (style.position === 'fixed' && parseFloat(style.zIndex) > 10) {
                overlays.push(div);
            }
        });
        
        // 2. Hide modal and overlays
        let original_modal_style = modal ? modal.style.display : null;
        if (modal) modal.style.display = 'none';
        
        let original_overlay_styles = overlays.map(o => ({ el: o, display: o.style.display }));
        overlays.forEach(o => o.style.display = 'none');
        
        // 3. Get current performance entries
        let res_before = performance.getEntries().map(e => e.name);
        
        // 4. Click Instructions button
        let btn = document.getElementById('starshot_instructions_button');
        if (btn) {
            btn.click();
            results.click_status = "Clicked Instructions button";
        } else {
            results.click_status = "Instructions button not found";
        }
        
        // We will return a promise to wait for a bit before checking DOM and restoring
        return new Promise((resolve) => {
            setTimeout(() => {
                // Get page text and new resources
                results.body_text = document.body.innerText.substring(0, 3000);
                
                let res_after = performance.getEntries().map(e => e.name);
                results.new_resources = res_after.filter(r => !res_before.includes(r));
                
                // Check if any new iframes or instructions divs appeared
                let instruction_divs = [];
                document.querySelectorAll('div, iframe').forEach(el => {
                    let text = el.innerText || '';
                    let id = el.id || '';
                    let className = el.className || '';
                    if (id.toLowerCase().includes('instruction') || className.toLowerCase().includes('instruction')) {
                        instruction_divs.push({ tag: el.tagName, id, className, text: text.substring(0, 1000) });
                    }
                });
                results.instruction_divs = instruction_divs;
                
                // 5. Restore modal and overlays
                if (modal) modal.style.display = original_modal_style;
                original_overlay_styles.forEach(item => {
                    item.el.style.display = item.display;
                });
                
                resolve(JSON.stringify(results));
            }, 3000);
        });
    })()
    """
    
    print("Executing instructions click hack...")
    res_str = evaluate(hack_js)
    if res_str:
        res = json.loads(res_str)
        print("Click Status:", res.get('click_status'))
        print("\nNew Resources loaded:", res.get('new_resources'))
        
        print("\n=== PAGE TEXT WITH MODAL HIDDEN ===")
        print(res.get('body_text'))
        print("====================================")
        
        print("\n=== INSTRUCTION DIVS ===")
        for d in res.get('instruction_divs', []):
            print(f"- [{d['tag']}] ID: {d['id']}, Class: {d['className']}")
            print(f"  Text: {d['text'][:400]}")
            print("-" * 30)
    else:
        print("Failed to run hack JS.")
        
    ws.close()

if __name__ == "__main__":
    main()
