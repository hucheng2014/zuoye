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
    
    def evaluate(js):
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
                return data.get("result", {}).get("result", {}).get("value", "")

    # Extract names live
    js_extract = """(() => {
        let textareas = Array.from(document.querySelectorAll("textarea")).map(ta => ta.name);
        let radioNames = Array.from(new Set(Array.from(document.querySelectorAll("input[type=radio]")).map(r => r.name)));
        return {textareas, radioNames};
    })()"""
    dom_names = evaluate(js_extract)
    radio_names = dom_names.get("radioNames", [])
    textarea_names = dom_names.get("textareas", [])
    
    print(f"\n--- Final Verification Before Click for {record_path} ---")
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
        print(f"Task {idx}: Radio '{rating}' checked: {radio_checked} | Comment matched: {comment_ok}")
        if not radio_checked or not comment_ok:
            verification_success = False
            
    if not verification_success:
        print("\nERROR: Verification failed. Page is not properly filled. Aborting submission.")
        ws.close()
        sys.exit(1)
        
    print("\nVerification PASSED! Clicking the Submit button...")
    
    # Click submit button
    submit_js = """(() => {
        let buttons = Array.from(document.querySelectorAll("button"));
        let submitBtn = buttons.find(b => b.textContent.trim().toLowerCase().includes("submit rating"));
        if (submitBtn) {
            submitBtn.click();
            return "Clicked Submit Rating";
        }
        return "Submit Rating button NOT found";
    })()"""
    submit_res = evaluate(submit_js)
    print(f"Submission status: {submit_res}")
    
    # Wait for submission to process
    time.sleep(3)
    
    # Check if there are error banners on the page
    check_errors_js = """(() => {
        let text = document.body.innerText || "";
        if (text.includes("This field is required!")) return "Required errors present";
        if (text.includes("Validation failed!")) return "Validation failed pop-up present";
        return "No errors visible";
    })()"""
    post_submit_status = evaluate(check_errors_js)
    print(f"Post-submit validation status: {post_submit_status}")
    
    # Update local record JSON file
    batch_data["submit"]["authorized_by_user"] = True
    batch_data["submit"]["submitted"] = True
    batch_data["submit"]["submitted_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    batch_data["submit"]["post_submit_status"] = post_submit_status
    
    with open(record_path, "w", encoding="utf-8") as f:
        json.dump(batch_data, f, indent=2, ensure_ascii=False)
    print(f"Record JSON file updated at {record_path}")
    
    ws.close()

if __name__ == "__main__":
    main()
