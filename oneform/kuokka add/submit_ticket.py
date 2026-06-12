import json
import urllib.request
import time
import sys
import base64
import os
from websocket import create_connection

def main():
    persist_dir = "/Users/xaa/zuoye/oneform/kuokka add"
    screenshot_path = os.path.join(persist_dir, "workspace_loaded.png")
    
    if not os.path.exists(screenshot_path):
        print(f"Error: Screenshot file not found at {screenshot_path}")
        sys.exit(1)
        
    ws_url = "ws://127.0.0.1:9233/devtools/page/47A7A5FE9C866D76A69366F322A9B073"
    print(f"Connecting to Global Query tab: {ws_url}")
    try:
        ws = create_connection(ws_url, timeout=30)
    except Exception as e:
        print("Failed to connect to browser tab:", e)
        sys.exit(1)
        
    # Enable necessary domains
    ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
    ws.recv()
    ws.send(json.dumps({"id": 2, "method": "Runtime.enable"}))
    ws.recv()
    ws.send(json.dumps({"id": 3, "method": "DOM.enable"}))
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

    # 1. Navigate to bug report page
    print("Navigating to bug report page...")
    ws.send(json.dumps({
        "id": 10,
        "method": "Page.navigate",
        "params": {"url": "https://globalquery.oneforma.com/bug_report_page.php"}
    }))
    ws.recv()
    
    # Wait for page load
    time.sleep(4)
    
    # 2. Fill the form inputs via JavaScript
    print("Filling the form fields...")
    fill_js = """
    (() => {
        try {
            // Set Category: Other topics (value 1365)
            let categorySelect = document.querySelector('select[name="category_id"]');
            if (categorySelect) {
                categorySelect.value = "1365";
                // Trigger change event
                categorySelect.dispatchEvent(new Event('change', { bubbles: true }));
            }
            
            // Set Summary
            let summaryInput = document.querySelector('input[name="summary"]');
            if (summaryInput) {
                summaryInput.value = "URGENT: Account pipeline blocked by wrong project tasks (Kuokka Add - ms_MY)";
            }
            
            // Set Description
            let descInput = document.querySelector('textarea[name="description"]');
            if (descInput) {
                descInput.value = `Hi team,\\nWhen I logged into the client tool and clicked "Start Grading," my dashboard was completely blocked by a task from a different project: "Kuokka Add" in the ms_MY (Malaysian) locale.\\nDue to the language issue, I had to skip some tasks, but the tool is still continuously pushing the same wrong workflow. This is entirely blocking my access to the Isaac Lighthouse workflows.\\nCould you please coordinate with the PMs to manually remove the Kuokka/Jellyfish project skills from my profile entirely so I can return to my correct production queue? Thank you for your urgent support.\\n* User ID / Registered Email: jianglei1998@gmail.com`;
            }
            
            // Set Applicable Language(s) (custom_field_234 = ms_MY)
            let langSelect = document.querySelector('select[name="custom_field_234"]');
            if (langSelect) {
                langSelect.value = "ms_MY";
                langSelect.dispatchEvent(new Event('change', { bubbles: true }));
            }
            
            // Set Screenshot Confirm (custom_field_241 = Yes)
            let screenshotConfirm = document.querySelector('select[name="custom_field_241"]');
            if (screenshotConfirm) {
                screenshotConfirm.value = "Yes";
                screenshotConfirm.dispatchEvent(new Event('change', { bubbles: true }));
            }
            
            // Set URL (custom_field_287 = starshot broker url)
            let urlInput = document.querySelector('input[name="custom_field_287"]');
            if (urlInput) {
                urlInput.value = "https://starshot.scilliance.com/?broker=true";
            }
            
            return "Form fields populated successfully";
        } catch(e) {
            return "Error filling form: " + e.message;
        }
    })()
    """
    fill_res = evaluate(fill_js)
    print("Fill status:", fill_res)
    
    # 3. Set the file input to upload the screenshot
    print("Uploading screenshot file via CDP DOM domain...")
    
    # Get document
    ws.send(json.dumps({"id": 11, "method": "DOM.getDocument"}))
    root_node_id = None
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == 11:
            root_node_id = data.get("result", {}).get("root", {}).get("nodeId")
            break
            
    if not root_node_id:
        print("Failed to get DOM document.")
        ws.close()
        sys.exit(1)
        
    # Find file input nodeId
    ws.send(json.dumps({
        "id": 12,
        "method": "DOM.querySelector",
        "params": {
            "nodeId": root_node_id,
            "selector": "input[type='file']"
        }
    }))
    file_node_id = None
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == 12:
            file_node_id = data.get("result", {}).get("nodeId")
            break
            
    if not file_node_id:
        print("File input element not found in DOM.")
    else:
        # Set file input value using absolute path
        ws.send(json.dumps({
            "id": 13,
            "method": "DOM.setFileInputFiles",
            "params": {
                "nodeId": file_node_id,
                "files": [screenshot_path]
            }
        }))
        ws.recv()
        print("File successfully attached.")
        
    # 4. Click Submit Issue
    print("Clicking Submit Issue button...")
    click_submit_js = """
    (() => {
        let btn = document.querySelector('input[type="submit"]');
        if (btn) {
            btn.click();
            return "Clicked submit button";
        }
        return "Submit button not found";
    })()
    """
    print("Submit status:", evaluate(click_submit_js))
    
    # Wait for submit to process and page to navigate (usually 5 seconds)
    print("Waiting 5 seconds for submission to complete...")
    time.sleep(5)
    
    # Get final URL and take screenshot
    final_url = evaluate("location.href")
    print(f"Final URL after submission: {final_url}")
    
    # Take screenshot of the submission result page
    ws.send(json.dumps({
        "id": 300,
        "method": "Page.captureScreenshot",
        "params": {"format": "png"}
    }))
    img_data = None
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == 300:
            img_data = data.get("result", {}).get("data")
            break
            
    if img_data:
        res_screenshot_path = os.path.join(persist_dir, "global_query_submitted.png")
        with open(res_screenshot_path, "wb") as f:
            f.write(base64.b64decode(img_data))
        print(f"Saved submission result screenshot to: {res_screenshot_path}")
        os.system(f'cp "{res_screenshot_path}" "/Users/xaa/.gemini/antigravity-cli/brain/7f207531-9de7-4f95-9c38-e583af332566/global_query_submitted.png"')
    
    ws.close()

if __name__ == "__main__":
    main()
