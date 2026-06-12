import json
import urllib.request
import time
import sys
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
    print(f"Connecting to page: {page['title']} ({ws_url})")
    
    ws = create_connection(ws_url, timeout=30)
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

    # 1. Inspect React state to find locale and url
    print("Checking current task locale and asset URL...")
    react_check_js = """
    (() => {
        let iframe = document.querySelector('iframe');
        if (!iframe) return JSON.stringify({ error: "No iframe found" });
        
        try {
            let doc = iframe.contentDocument || iframe.contentWindow.document;
            let root = doc.querySelector('#root') || doc.body;
            let keys = Object.keys(root);
            let containerKey = keys.find(k => k.startsWith('__reactContainer') || k.startsWith('__reactFiber'));
            if (!containerKey) return JSON.stringify({ error: "No React Container key found" });
            
            let fiber = root[containerKey];
            let foundTask = null;
            
            function traverseFiber(node) {
                if (!node || foundTask) return;
                let props = node.memoizedProps;
                let state = node.memoizedState;
                if (props && props.task) {
                    foundTask = props.task;
                }
                if (state && state.task) {
                    foundTask = state.task;
                }
                if (node.child) traverseFiber(node.child);
                if (node.sibling) traverseFiber(node.sibling);
            }
            traverseFiber(fiber);
            
            if (!foundTask) return JSON.stringify({ error: "Task data not found in React tree" });
            
            let audio = (foundTask.assets && foundTask.assets.audio && foundTask.assets.audio[0]) || {};
            return JSON.stringify({
                locale: audio.localeId || "unknown",
                url: audio.url || "none"
            });
        } catch(e) {
            return JSON.stringify({ error: e.message });
        }
    })()
    """
    
    task_info_str = evaluate(react_check_js)
    if not task_info_str:
        print("Failed to evaluate React task details.")
        ws.close()
        sys.exit(1)
        
    task_info = json.loads(task_info_str)
    if "error" in task_info:
        print(f"React extraction error: {task_info['error']}")
        ws.close()
        sys.exit(1)
        
    locale = task_info.get("locale", "unknown")
    url = task_info.get("url", "none")
    print(f"\n[TASK INFO] Current task language locale: {locale}")
    print(f"[TASK INFO] Current audio URL: {url}")
    
    # Check if Chinese or English
    locale_lower = locale.lower()
    if locale_lower.startswith("zh") or locale_lower.startswith("en"):
        print(f"\n[SAFE GUARD] Current language is {locale} (Chinese/English). You can do this task! Script will NOT skip. Exiting safely...")
        ws.close()
        sys.exit(0)
        
    print(f"\n[SAFE GUARD] Current language is {locale} (Non-English/Non-Chinese). Program will proceed to automatically skip...")
    
    # 2. Enter workspace if not already there
    lobby_check_js = """
    (() => {
        let btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Start');
        if (btn) {
            btn.click();
            return "Clicked Start to enter workspace";
        }
        return "Already in workspace";
    })()
    """
    print(evaluate(lobby_check_js))
    time.sleep(5)
    
    # 3. Click 'Report a Problem' button
    click_report_menu_js = """
    (() => {
        let btn = Array.from(document.querySelectorAll('button')).find(b => b.getAttribute('aria-label') === 'Report a Problem');
        if (btn) {
            btn.click();
            return "Clicked Report a Problem menu";
        }
        return "Report a Problem button not found";
    })()
    """
    print(evaluate(click_report_menu_js))
    time.sleep(1.5)
    
    # 4. Click 'Report Task'
    click_report_task_js = """
    (() => {
        let btn = Array.from(document.querySelectorAll('button, a, div, span')).find(b => b.innerText && b.innerText.trim() === 'Report Task');
        if (btn) {
            btn.click();
            return "Clicked Report Task";
        }
        return "Report Task button not found";
    })()
    """
    print(evaluate(click_report_task_js))
    time.sleep(1.5)
    
    # 5. Select 'Expertise Mismatch' and click 'Submit'
    skip_submit_js = """
    (() => {
        // Select 'Expertise Mismatch'
        let optionText = 'Expertise Mismatch';
        let optionEl = Array.from(document.querySelectorAll('label, span, div, p')).find(el => {
            return el.innerText && el.innerText.trim() === optionText;
        });
        
        if (!optionEl) return "Option element 'Expertise Mismatch' not found";
        
        optionEl.click();
        let input = optionEl.querySelector('input') || 
                    (optionEl.parentElement && optionEl.parentElement.querySelector('input'));
        if (input) input.click();
        
        // Click Submit
        let submitBtn = Array.from(document.querySelectorAll('button, div, span')).find(b => {
            return b.innerText && b.innerText.trim() === 'Submit';
        });
        
        if (!submitBtn) return "Submit button not found";
        submitBtn.click();
        return "Successfully selected Expertise Mismatch and clicked Submit";
    })()
    """
    print(evaluate(skip_submit_js))
    
    # Wait for skip to finish
    print("Waiting 3 seconds for skip to process...")
    time.sleep(3)
    
    # Verification
    verify_js = "document.body.innerText"
    print("\n=== PAGE TEXT AFTER SKIP ===")
    print(repr(evaluate(verify_js)))
    
    ws.close()

if __name__ == "__main__":
    main()
