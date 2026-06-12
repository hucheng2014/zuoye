#!/usr/bin/env python3
"""每小时点击 Check Now 并检测是否有新题"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime

CDP_ENDPOINT = os.environ.get("CDP_ENDPOINT", "http://browser:9223")
NOTIFY_FILE = "/app/task_alert.flag"

def get_pages():
    req = urllib.request.Request(f"{CDP_ENDPOINT}/json/list")
    req.add_header("Host", "localhost:9222")
    resp = urllib.request.urlopen(req, timeout=5)
    return json.loads(resp.read())

def evaluate(ws, js):
    from websocket import create_connection
    ws.send(json.dumps({"id": 99, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True, "awaitPromise": True}}))
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == 99:
            return data.get("result", {}).get("result", {}).get("value", "")

def check_and_click():
    from websocket import create_connection
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] Checking for new tasks...")

    try:
        pages = get_pages()
    except Exception as e:
        print(f"  ERROR: Cannot connect to browser: {e}")
        return False

    for page in pages:
        if page.get("type") != "page":
            continue
        url = page.get("url", "")
        if "tryrating" not in url and "survey" not in url:
            continue

        ws_url = page["webSocketDebuggerUrl"].replace("ws://localhost:9222", "ws://browser:9223")
        try:
            ws = create_connection(ws_url, timeout=10)
            ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
            ws.recv()

            # Click "Check Now" button if present
            click_js = '''(() => {
                let btns = document.querySelectorAll('button');
                for (let b of btns) {
                    if (b.textContent.trim().toLowerCase().includes('check now')) {
                        b.click();
                        return 'clicked';
                    }
                }
                return 'no button';
            })()'''
            result = evaluate(ws, click_js)
            print(f"  Page: {url[:60]} | Click: {result}")

            if result == 'clicked':
                # Wait for page to update
                time.sleep(5)

            # Check page content
            check_js = '''(() => {
                let text = document.body.innerText || '';
                if (text.includes('No more surveys')) return 'no_tasks';
                if (text.includes('QUERY') && text.includes('RESULT AD')) return 'AD_TASKS';
                if (text.includes('keyword') && text.includes('expansion')) return 'ADJIAN_TASKS';
                if (text.toLowerCase().includes('rate') && !text.includes('No more')) return 'POSSIBLE_TASKS';
                return 'unknown: ' + text.substring(0, 100);
            })()'''
            status = evaluate(ws, check_js)
            print(f"  Status: {status}")
            ws.close()

            if 'TASKS' in status.upper() and 'no_tasks' not in status:
                print(f"  >>> NEW TASKS FOUND: {status} <<<")
                # Write alert flag
                with open(NOTIFY_FILE, "w") as f:
                    f.write(f"{now}|{status}\n")
                return True

        except Exception as e:
            print(f"  Error checking page: {e}")

    # No tasks - remove flag if exists
    if os.path.exists(NOTIFY_FILE):
        os.remove(NOTIFY_FILE)
    print(f"[{now}] No new tasks. Will re-check in 5s.")
    return False

if __name__ == "__main__":
    check_and_click()
