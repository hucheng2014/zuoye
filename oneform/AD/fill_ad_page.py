#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.request
from websocket import create_connection

def main():
    if len(sys.argv) > 1:
        record_path = sys.argv[1]
    else:
        record_path = "records/2026-06-01_batch_001.json"
        
    if not os.path.exists(record_path):
        print(f"Error: Record file {record_path} does not exist.")
        sys.exit(1)
        
    with open(record_path, "r", encoding="utf-8") as f:
        batch_data = json.load(f)
        
    CDP_ENDPOINT = "http://browser:9223"
    print(f"Connecting to browser at {CDP_ENDPOINT}...")
    try:
        req = urllib.request.Request(f"{CDP_ENDPOINT}/json/list")
        req.add_header("Host", "localhost:9222")
        resp = urllib.request.urlopen(req, timeout=5)
        pages = json.loads(resp.read())
    except Exception as e:
        print(f"Failed to list browser tabs: {e}")
        sys.exit(1)
        
    page = [p for p in pages if p.get("type") == "page" and ("tryrating" in p.get("url", "") or "survey" in p.get("url", ""))][0]
    ws_url = page["webSocketDebuggerUrl"].replace("ws://localhost:9222", "ws://browser:9223")
    print(f"Connecting to page WS: {ws_url}")
    ws = create_connection(ws_url, timeout=15)
    
    # Enable domains
    ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
    ws.recv()
    ws.send(json.dumps({"id": 2, "method": "Input.enable"}))
    ws.recv()
    
    def evaluate(js, return_raw=False):
        cmd_id = 999
        ws.send(json.dumps({
            "id": cmd_id,
            "method": "Runtime.evaluate",
            "params": {"expression": js, "returnByValue": True, "awaitPromise": True}
        }))
        while True:
            raw = ws.recv()
            data = json.loads(raw)
            if data.get("id") == cmd_id:
                if return_raw:
                    return data
                return data.get("result", {}).get("result", {}).get("value", "")

    # Extract names live
    js_extract = """(() => {
        let textareas = Array.from(document.querySelectorAll("textarea")).map(ta => ta.name);
        let radioNames = Array.from(new Set(Array.from(document.querySelectorAll("input[type=radio]")).map(r => r.name)));
        return {textareas, radioNames};
    })()"""
    dom_names = evaluate(js_extract)
    print("Live DOM Names Extracted:")
    print("Radio groups:", dom_names.get("radioNames"))
    print("Textareas:", dom_names.get("textareas"))
    
    radio_names = dom_names.get("radioNames", [])
    textarea_names = dom_names.get("textareas", [])
    
    if len(radio_names) < len(batch_data["tasks"]) or len(textarea_names) < len(batch_data["tasks"]):
        print(f"Error: Could not extract names for all {len(batch_data['tasks'])} tasks from DOM (found {len(radio_names)} radios, {len(textarea_names)} textareas).")
        sys.exit(1)

    print(f"\n--- Starting to fill the page from {record_path} ---")
    for idx_0, t in enumerate(batch_data["tasks"]):
        idx = t["index"] # 1-based index
        req_id = t["task_id"]
        query = t["query"]
        ad_name = t["ad"]["name"]
        rating = t["rating"].lower()
        comment = t["comment"]
        
        radio_name = radio_names[idx_0]
        textarea_name = textarea_names[idx_0]
        
        print(f"Task {idx} (Req ID: {req_id}, Query: {query}, Ad: {ad_name})")
        print(f"  Rating: {rating} (Radio: {radio_name})")
        print(f"  Comment: {comment[:60]}...")
        
        # Click Radio button
        click_js = f"""(() => {{
            let r = document.querySelector("input[type=radio][name='{radio_name}'][value='{rating}']");
            if (!r) return "Radio NOT found";
            r.click();
            r.checked = true;
            r.dispatchEvent(new Event("change", {{bubbles: true}}));
            return "Clicked";
        }})()"""
        click_res = evaluate(click_js)
        print(f"  -> Click Radio Status: {click_res}")
        
        # Focus and Click Textarea
        focus_js = f"""(() => {{
            let ta = document.querySelector("textarea[name='{textarea_name}']");
            if (!ta) return "Textarea NOT found";
            ta.focus();
            ta.click();
            return "Focused";
        }})()"""
        focus_res = evaluate(focus_js)
        print(f"  -> Focus Textarea Status: {focus_res}")
        
        # Insert Comment text using Input.insertText
        ws.send(json.dumps({
            "id": 100 + idx,
            "method": "Input.insertText",
            "params": {"text": ""}
        }))
        ws.recv()
        
        # Clear value first
        clear_js = f"""(() => {{
            let ta = document.querySelector("textarea[name='{textarea_name}']");
            if (ta) ta.value = "";
        }})()"""
        evaluate(clear_js)
        
        # Re-focus and insert text
        evaluate(focus_js)
        ws.send(json.dumps({
            "id": 200 + idx,
            "method": "Input.insertText",
            "params": {"text": comment}
        }))
        ws.recv()
        
        # Blur the textarea
        blur_js = f"""(() => {{
            let ta = document.querySelector("textarea[name='{textarea_name}']");
            if (ta) ta.blur();
        }})()"""
        evaluate(blur_js)
        
        time.sleep(1)
        
    print("\n--- Verifying page values ---")
    verification_success = True
    for idx_0, t in enumerate(batch_data["tasks"]):
        idx = t["index"]
        radio_name = radio_names[idx_0]
        rating = t["rating"].lower()
        textarea_name = textarea_names[idx_0]
        expected_comment = t["comment"]
        
        # Check Radio status
        check_radio_js = f"""(() => {{
            let r = document.querySelector("input[type=radio][name='{radio_name}'][value='{rating}']");
            return r ? r.checked : false;
        }})()"""
        radio_checked = evaluate(check_radio_js)
        
        # Check Textarea value
        check_ta_js = f"""(() => {{
            let ta = document.querySelector("textarea[name='{textarea_name}']");
            return ta ? ta.value : "";
        }})()"""
        actual_comment = evaluate(check_ta_js)
        
        comment_ok = (actual_comment.strip() == expected_comment.strip())
        print(f"Task {idx}:")
        print(f"  Radio '{rating}' checked: {radio_checked} (Expected: True)")
        print(f"  Comment matched: {comment_ok} (Actual length: {len(actual_comment.strip())}, Expected length: {len(expected_comment.strip())})")
        
        if not radio_checked or not comment_ok:
            verification_success = False
            
    if verification_success:
        print("\nSUCCESS: All ratings and comments filled and verified successfully on the page!")
    else:
        print("\nWARNING: Some fields were not successfully filled or verified. Please check manually.")
        
    ws.close()

if __name__ == "__main__":
    main()
