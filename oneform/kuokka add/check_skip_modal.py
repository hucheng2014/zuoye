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

    # 1. Click Start, Click Report a Problem, Click Report Task to open the skip modal again
    print("Opening skip modal...")
    open_js = """
    (() => {
        // Hide overlay if shown
        document.querySelectorAll('div').forEach(el => {
            if (el.style.display === 'none') el.style.display = '';
        });
        
        let startBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Start');
        if (startBtn) startBtn.click();
    })()
    """
    evaluate(open_js)
    time.sleep(4)
    
    open_report_js = """
    (() => {
        let btn = Array.from(document.querySelectorAll('button')).find(b => b.getAttribute('aria-label') === 'Report a Problem');
        if (btn) btn.click();
    })()
    """
    evaluate(open_report_js)
    time.sleep(1.5)
    
    open_report_task_js = """
    (() => {
        let btn = Array.from(document.querySelectorAll('button, a, div, span')).find(b => b.innerText && b.innerText.trim() === 'Report Task');
        if (btn) btn.click();
    })()
    """
    evaluate(open_report_task_js)
    time.sleep(1.5)
    
    # 2. Inspect modal elements
    print("Inspecting modal DOM elements...")
    inspect_js = """
    (() => {
        let inputs = [];
        document.querySelectorAll('input').forEach((el, idx) => {
            let label = el.parentElement ? el.parentElement.innerText.trim() : '';
            inputs.push({
                index: idx,
                type: el.type,
                name: el.name,
                checked: el.checked,
                label: label,
                value: el.value,
                className: el.className
            });
        });
        
        let buttons = [];
        document.querySelectorAll('button').forEach(btn => {
            buttons.push({
                text: btn.innerText.trim(),
                className: btn.className,
                disabled: btn.disabled
            });
        });
        
        return JSON.stringify({
            inputs: inputs,
            buttons: buttons
        });
    })()
    """
    
    res_str = evaluate(inspect_js)
    if res_str:
        res = json.loads(res_str)
        print("\n=== INPUTS FOUND ===")
        for i in res.get("inputs", []):
            print(f"- Input {i['index']}: type: {i['type']}, label: {repr(i['label'])}, checked: {i['checked']}, value: {repr(i['value'])}")
            
        print("\n=== BUTTONS FOUND ===")
        for b in res.get("buttons", []):
            print(f"- Button: {repr(b['text'])}, disabled: {b['disabled']}")
    else:
        print("Failed to inspect modal.")
        
    ws.close()

if __name__ == "__main__":
    main()
