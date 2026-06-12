import json
import urllib.request
import time
import sys
import os
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
                res = data.get("result", {})
                if "exceptionDetails" in res:
                    print("JS Error:", res["exceptionDetails"])
                    return None
                return res.get("result", {}).get("value")

    loop_count = 0
    while True:
        loop_count += 1
        print(f"\n==============================================")
        print(f"LOOP #{loop_count}: Reloading page to fetch a new task...")
        print(f"==============================================")
        
        ws.send(json.dumps({"id": 4, "method": "Page.reload"}))
        try:
            ws.recv()
        except Exception: pass
        
        # Wait for page elements to load
        time.sleep(6)
        
        # Check if we got a task (look for Start button or body text)
        body_text = evaluate("document.body.innerText") or ""
        
        # Check if task is loaded
        if "New Task" in body_text or "Start" in body_text or "Instructions" in body_text:
            print("Task assigned! Extracting language metadata...")
            
            # Inspect React state to find locale and url
            react_check_js = """
            (() => {
                let iframe = document.querySelector('iframe');
                if (!iframe) return JSON.stringify({ error: "No iframe found" });
                try {
                    let doc = iframe.contentDocument || iframe.contentWindow.document;
                    let root = doc.querySelector('#root') || doc.body;
                    let keys = Object.keys(root);
                    let containerKey = keys.find(k => k.startsWith('__reactContainer') || k.startsWith('__reactFiber'));
                    if (!containerKey) return JSON.stringify({ error: "No React Container found" });
                    
                    let fiber = root[containerKey];
                    let foundTask = null;
                    
                    function traverseFiber(node) {
                        if (!node || foundTask) return;
                        let props = node.memoizedProps;
                        let state = node.memoizedState;
                        if (props && props.task) foundTask = props.task;
                        if (state && state.task) foundTask = state.task;
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
                print("Failed to check React state. Retrying in next loop...")
                continue
                
            task_info = json.loads(task_info_str)
            if "error" in task_info:
                print(f"React check returned error: {task_info['error']}. Retrying in next loop...")
                continue
                
            locale = task_info.get("locale", "unknown")
            url = task_info.get("url", "none")
            print(f"-> Language Locale: {locale}")
            print(f"-> Audio URL: {url}")
            
            locale_lower = locale.lower()
            # SAFE GUARD CHECK
            if locale_lower.startswith("zh") or locale_lower.startswith("en"):
                print(f"\n[ALERT] MATCH FOUND! Current task is {locale} (Chinese/English).")
                print("Stopping the auto-skip loop and preserving the task on screen!")
                # Beep to alert the user (Linux compatible terminal beep)
                for _ in range(5):
                    sys.stdout.write('\a')
                    sys.stdout.flush()
                    time.sleep(0.5)
                break
                
            # Else, it's a foreign language, skip it
            print(f"-> Language {locale} is NOT Chinese/English. Initiating skip...")
            
            # Click Start to enter workspace
            click_start_js = """
            (() => {
                let btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Start');
                if (btn) {
                    btn.click();
                    return "Clicked Start";
                }
                return "Already in workspace";
            })()
            """
            print(f"   {evaluate(click_start_js)}")
            time.sleep(4)
            
            # Click Report a Problem
            click_report_menu_js = """
            (() => {
                let btn = Array.from(document.querySelectorAll('button')).find(b => b.getAttribute('aria-label') === 'Report a Problem');
                if (btn) {
                    btn.click();
                    return "Clicked Report a Problem";
                }
                return "Report button not found";
            })()
            """
            print(f"   {evaluate(click_report_menu_js)}")
            time.sleep(1.5)
            
            # Click Report Task
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
            print(f"   {evaluate(click_report_task_js)}")
            time.sleep(1.5)
            
            # Select Expertise Mismatch and Submit
            skip_submit_js = """
            (() => {
                let optionText = 'Expertise Mismatch';
                let optionEl = Array.from(document.querySelectorAll('label, span, div, p')).find(el => {
                    return el.innerText && el.innerText.trim() === optionText;
                });
                if (!optionEl) return "Option element not found";
                optionEl.click();
                let input = optionEl.querySelector('input') || 
                            (optionEl.parentElement && optionEl.parentElement.querySelector('input'));
                if (input) input.click();
                
                let submitBtn = Array.from(document.querySelectorAll('button, div, span')).find(b => {
                    return b.innerText && b.innerText.trim() === 'Submit';
                });
                if (!submitBtn) return "Submit button not found";
                submitBtn.click();
                return "Successfully submitted skip";
            })()
            """
            print(f"   {evaluate(skip_submit_js)}")
            
            # Wait for skip to register
            print("   Waiting 3 seconds for skip to register...")
            time.sleep(3)
            
        else:
            print("No active task loaded (page might be loading or no tasks available).")
            print("Waiting 15 seconds before trying again...")
            time.sleep(15)
            
    ws.close()
    print("\n[LOOP STOPPED] Tab is preserved at a valid task.")

if __name__ == "__main__":
    main()
