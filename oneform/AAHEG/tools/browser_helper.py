#!/usr/bin/env python3
"""
AAHEG Browser Helper - 用于 TryRating 做题的浏览器交互工具。
通过 CDP 连接 Docker 中的 Chrome 浏览器，读取题目、填写评分、提交。

使用方式（由 Claude 在 bash 中调用）：
    python3 tools/browser_helper.py read_task
    python3 tools/browser_helper.py fill_rating '{"accuracy":"Correct","relevancy":"Pass",...}'
    python3 tools/browser_helper.py submit
    python3 tools/browser_helper.py screenshot [filename]
    python3 tools/browser_helper.py wait_and_submit   # 等待计时器结束后提交
"""
import sys
import json
import time
import os
import re
from datetime import datetime

CDP_ENDPOINT = os.environ.get("CDP_ENDPOINT", "http://172.19.0.3:9223")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
SCREENSHOT_DIR = os.path.join(PROJECT_DIR, "screenshots")
TASK_LOG_FILE = os.path.join(PROJECT_DIR, "task_log.jsonl")
MIN_RATING_SECONDS = 155  # 2m35s, slightly over 2m30s requirement

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def get_page():
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(CDP_ENDPOINT)
    context = browser.contexts[0]
    page = context.pages[0]
    return pw, browser, page

def read_task():
    """读取当前题目内容：Task ID、Question、Answer、Cited Resources"""
    pw, browser, page = get_page()
    try:
        body_text = page.inner_text("body")

        # Extract Task ID
        task_id = ""
        m = re.search(r'Task ID\s*\n\s*(\S+)', body_text)
        if m:
            task_id = m.group(1)

        # Extract Question
        question = ""
        m = re.search(r'Questions?:\s*(.+?)(?:\n\n|\nAnswer)', body_text, re.DOTALL)
        if m:
            question = m.group(1).strip()

        # Extract Answer
        answer = ""
        m = re.search(r'Answer:\s*\n(.+?)(?:\nAre the factual|\nBrowse it)', body_text, re.DOTALL)
        if m:
            answer = m.group(1).strip()

        # Extract Cited Resources (links in the page)
        html = page.content()
        cited_links = []
        # Look for apple.com links in task content (often inside iframe or encoded HTML)
        for link_match in re.finditer(r'href=["\']?(https?://[^"\'>\s]+apple[^"\'>\s]*)', html):
            url = link_match.group(1).replace('&amp;', '&')
            if url not in cited_links:
                cited_links.append(url)
        # Also check for encoded links
        for link_match in re.finditer(r'href=&quot;(https?://[^&]+apple[^&]*?)&quot;', html):
            url = link_match.group(1)
            if url not in cited_links:
                cited_links.append(url)

        # Check if there's an iframe with "Browse it" content
        browse_text = ""
        iframes = page.query_selector_all("iframe")
        for iframe in iframes:
            try:
                frame = iframe.content_frame()
                if frame:
                    ft = frame.inner_text("body")
                    if ft.strip():
                        browse_text = ft.strip()[:2000]
            except:
                pass

        # Check current form state (what's already selected)
        form_state = _read_form_state(page)

        result = {
            "task_id": task_id,
            "question": question,
            "answer": answer,
            "cited_links": cited_links,
            "browse_text": browse_text,
            "form_state": form_state,
            "timestamp": datetime.now().isoformat()
        }

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    finally:
        browser.close()
        pw.stop()

def _read_form_state(page):
    """读取当前表单已选状态"""
    state = {}
    radios = page.query_selector_all("input[type='radio']:checked")
    for r in radios:
        name = r.get_attribute("name") or ""
        value = r.get_attribute("value") or ""
        state[name] = value
    checkboxes = page.query_selector_all("input[type='checkbox']:checked")
    cb_values = {}
    for c in checkboxes:
        name = c.get_attribute("name") or ""
        value = c.get_attribute("value") or ""
        if name not in cb_values:
            cb_values[name] = []
        cb_values[name].append(value)
    state.update(cb_values)
    return state

# Field name mapping (these are dynamic per page, so we discover them)
def _discover_fields(page):
    """动态发现表单字段名称"""
    html = page.content()
    fields = {}

    # Accuracy - radio with "Correct" value
    acc = page.query_selector("input[type='radio'][value='Correct']")
    if acc:
        fields["accuracy"] = acc.get_attribute("name")

    # Relevancy - second radio group with Pass/Fail
    radio_groups = {}
    for r in page.query_selector_all("input[type='radio']"):
        name = r.get_attribute("name") or ""
        if name not in radio_groups:
            radio_groups[name] = []
        radio_groups[name].append(r.get_attribute("value"))

    # Accuracy is the one with "Correct"
    # Relevancy and Compliance are the ones with "Pass"/"Fail"
    pass_fail_groups = [name for name, vals in radio_groups.items()
                        if set(vals) == {"Pass", "Fail"}]

    # Find which is relevancy vs compliance by looking at label text
    for name in pass_fail_groups:
        radio_el = page.query_selector(f"input[name='{name}']")
        if radio_el:
            label_text = radio_el.evaluate("""el => {
                let form = el.closest('form');
                if (!form) form = el.closest('.ff-field-wrapper');
                if (!form) return '';
                let label = form.querySelector('label');
                return label ? label.textContent : '';
            }""")
            if "relevant" in label_text.lower():
                fields["relevancy"] = name
            elif "follow" in label_text.lower() or "terminology" in label_text.lower():
                fields["compliance"] = name

    # Safety - checkbox group
    cb = page.query_selector("input[type='checkbox']")
    if cb:
        fields["safety"] = cb.get_attribute("name")

    # Comment - text input
    txt = page.query_selector("input[type='text']")
    if txt:
        fields["comment"] = txt.get_attribute("name")

    # Fluency slider - find by label text
    for keyword, key in [("natural", "fluency"), ("quality", "quality")]:
        label_el = page.query_selector(f"label:has-text('{keyword}')")
        if label_el:
            for_attr = label_el.get_attribute("for")
            if for_attr:
                fields[key] = for_attr

    return fields

FLUENCY_MAP = {
    "Broken": 0, "0": 0,
    "Machine-translated feel": 25, "25": 25,
    "Unnatural but clear": 50, "50": 50,
    "Minor slips": 75, "75": 75,
    "Native": 100, "100": 100,
}

QUALITY_MAP = {
    "Broken": 0, "0": 0,
    "Bad": 25, "25": 25,
    "Neutral": 50, "50": 50,
    "Good": 75, "75": 75,
    "Very good": 100, "100": 100,
}

ACCURACY_VALUES = {"Correct": "Correct", "Not correct": "No", "Cannot verify": "Cannot verify", "N/A": "n/a"}
SAFETY_VALUES = {"Pass": ["100"], "Fail_a": ["a"], "Fail_b": ["b"], "Fail_c": ["c"]}

def fill_rating(rating_json_str):
    """
    填写评分。接受 JSON 字符串，所有条件字段自动处理。
    conditional rationale fields for Fail/non-max ratings are filled using
    the specific *_rationale key or falling back to comment.
    """
    import time as _t
    ratings = json.loads(rating_json_str)
    pw, browser, page = get_page()
    try:
        fields = _discover_fields(page)
        print(f"Discovered fields: {json.dumps(fields)}")

        # Track all known named fields to identify newly-appearing conditional inputs
        comment_name = fields.get("comment", "")

        def _fill_conditional_field(rationale_text, already_filled_names):
            """Wait and fill the first new empty visible text input (conditional field)."""
            _t.sleep(0.6)
            for inp in page.query_selector_all("input[type='text']"):
                inp_name = inp.get_attribute("name") or ""
                if inp_name not in already_filled_names and inp.is_visible():
                    current_val = inp.input_value()
                    if not current_val:
                        inp.fill(rationale_text)
                        print(f"  ✓ conditional field [{inp_name}]: {rationale_text[:70]}...")
                        already_filled_names.add(inp_name)
                        return inp_name
            return None

        filled_text_names = {comment_name}

        # 1. Accuracy
        if "accuracy" in ratings and "accuracy" in fields:
            value = ACCURACY_VALUES.get(ratings["accuracy"], ratings["accuracy"])
            el = page.query_selector(f"input[name='{fields['accuracy']}'][value='{value}']")
            if el:
                el.click()
                print(f"✓ Accuracy: {ratings['accuracy']}")
                if ratings["accuracy"] in ("Not correct", "Cannot verify"):
                    rationale = ratings.get("accuracy_rationale", ratings.get("comment", ""))
                    _fill_conditional_field(rationale, filled_text_names)
            else:
                print(f"✗ Accuracy: radio value '{value}' not found")

        # 2. Relevancy
        if "relevancy" in ratings and "relevancy" in fields:
            el = page.query_selector(f"input[name='{fields['relevancy']}'][value='{ratings['relevancy']}']")
            if el:
                el.click()
                print(f"✓ Relevancy: {ratings['relevancy']}")
                if ratings["relevancy"] == "Fail":
                    rationale = ratings.get("relevancy_rationale", ratings.get("comment", ""))
                    _fill_conditional_field(rationale, filled_text_names)
            else:
                print(f"✗ Relevancy: not found")

        # 3. Compliance
        if "compliance" in ratings and "compliance" in fields:
            el = page.query_selector(f"input[name='{fields['compliance']}'][value='{ratings['compliance']}']")
            if el:
                el.click()
                print(f"✓ Compliance: {ratings['compliance']}")
                if ratings["compliance"] == "Fail":
                    rationale = ratings.get("compliance_rationale", ratings.get("comment", ""))
                    _fill_conditional_field(rationale, filled_text_names)
            else:
                print(f"✗ Compliance: not found")

        # 4. Fluency (slider) — non-Native triggers a conditional field
        if "fluency" in ratings:
            _set_slider(page, "natural", ratings["fluency"], FLUENCY_MAP)
            if ratings["fluency"] != "Native":
                rationale = ratings.get("fluency_rationale", ratings.get("comment", ""))
                _fill_conditional_field(rationale, filled_text_names)

        # 5. Safety (checkboxes)
        if "safety" in ratings and "safety" in fields:
            safety_vals = ratings["safety"]
            if isinstance(safety_vals, str):
                safety_vals = [safety_vals]
            for cb in page.query_selector_all(f"input[name='{fields['safety']}']"):
                if cb.is_checked():
                    cb.click()
            for sv in safety_vals:
                cb_val = "100" if sv == "Pass" else sv.replace("Fail_", "") if sv.startswith("Fail_") else sv
                cb_el = page.query_selector(f"input[name='{fields['safety']}'][value='{cb_val}']")
                if cb_el:
                    cb_el.click()
                    print(f"✓ Safety: {sv}")
                else:
                    print(f"✗ Safety: '{cb_val}' not found")
            if any(sv != "Pass" for sv in safety_vals):
                rationale = ratings.get("safety_rationale", ratings.get("comment", ""))
                _fill_conditional_field(rationale, filled_text_names)

        # 6. Quality (slider) — non-Very-good may trigger conditional field
        if "quality" in ratings:
            _set_slider(page, "quality", ratings["quality"], QUALITY_MAP)
            if ratings["quality"] not in ("Very good", "100"):
                rationale = ratings.get("quality_rationale", ratings.get("comment", ""))
                _fill_conditional_field(rationale, filled_text_names)

        # 7. Comment (main bottom field)
        if "comment" in ratings and comment_name:
            comment_el = page.query_selector(f"input[name='{comment_name}']")
            if comment_el:
                comment_el.fill(ratings["comment"])
                print(f"✓ Comment: {ratings['comment'][:60]}...")

        # Final sweep: fill any remaining visible empty text inputs with comment text
        fallback = ratings.get("comment", "")
        if fallback:
            for inp in page.query_selector_all("input[type='text']"):
                inp_name = inp.get_attribute("name") or ""
                if inp_name not in filled_text_names and inp.is_visible() and not inp.input_value():
                    inp.fill(fallback)
                    print(f"  ✓ fallback fill [{inp_name}]: {fallback[:60]}...")
                    filled_text_names.add(inp_name)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ss_path = os.path.join(SCREENSHOT_DIR, f"filled_{ts}.png")
        page.screenshot(path=ss_path, full_page=True)
        print(f"Screenshot: {ss_path}")

    finally:
        browser.close()
        pw.stop()

def _set_slider(page, label_keyword, value_str, value_map):
    """点击 rc-slider 上的对应标记来设置滑块值"""
    target_pct = value_map.get(value_str)
    if target_pct is None:
        print(f"✗ Slider ({label_keyword}): unknown value '{value_str}'")
        return

    # Find the slider wrapper near the label containing the keyword
    label_el = page.query_selector(f"label:has-text('{label_keyword}')")
    if not label_el:
        print(f"✗ Slider ({label_keyword}): label not found")
        return

    wrapper = label_el.evaluate("""el => {
        let parent = el.closest('.ff-field-wrapper') || el.closest('form');
        return parent ? parent.className : null;
    }""")

    # Find the slider mark text that matches the target percentage
    form_el = label_el.evaluate_handle("""el => {
        return el.closest('form') || el.closest('.ff-field-wrapper');
    }""")

    # Click on the dot at the right position
    dot_selector = f"left: {target_pct}%"
    dots = form_el.query_selector_all(".rc-slider-dot")
    clicked = False
    for dot in dots:
        style = dot.get_attribute("style") or ""
        if f"left: {target_pct}%" in style:
            dot.click()
            clicked = True
            print(f"✓ Slider ({label_keyword}): {value_str} ({target_pct}%)")
            break

    if not clicked:
        # Fallback: click on the mark text
        marks = form_el.query_selector_all(".rc-slider-mark-text")
        for mark in marks:
            text = mark.inner_text().strip()
            if text.lower() == value_str.lower() or text.lower().startswith(value_str.lower()[:6]):
                mark.click()
                clicked = True
                print(f"✓ Slider ({label_keyword}): clicked mark text '{text}'")
                break

    if not clicked:
        print(f"✗ Slider ({label_keyword}): could not set to '{value_str}'")

def submit():
    """提交当前评分"""
    pw, browser, page = get_page()
    try:
        btn = page.query_selector("button:has-text('Submit Rating')")
        if btn:
            btn.click()
            print("✓ Submit Rating clicked")
            time.sleep(3)
            # Screenshot after submit
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            ss_path = os.path.join(SCREENSHOT_DIR, f"submitted_{ts}.png")
            page.screenshot(path=ss_path, full_page=True)
            print(f"Screenshot: {ss_path}")
            # Check new page state
            new_text = page.inner_text("body")[:500]
            print(f"Page after submit: {new_text[:200]}")
        else:
            print("✗ Submit button not found")
    finally:
        browser.close()
        pw.stop()

def wait_and_submit(start_time_iso=None):
    """等待到最小时间后提交"""
    if start_time_iso:
        start = datetime.fromisoformat(start_time_iso)
    else:
        start = datetime.now()
        print(f"Timer started at {start.isoformat()}")
        print(f"Will submit after {MIN_RATING_SECONDS} seconds ({MIN_RATING_SECONDS//60}m{MIN_RATING_SECONDS%60}s)")

    elapsed = (datetime.now() - start).total_seconds()
    remaining = max(0, MIN_RATING_SECONDS - elapsed)
    if remaining > 0:
        print(f"Waiting {remaining:.0f}s to meet minimum time requirement...")
        time.sleep(remaining)

    submit()

def screenshot(filename=None):
    """截图保存"""
    pw, browser, page = get_page()
    try:
        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screen_{ts}.png"
        path = os.path.join(SCREENSHOT_DIR, filename) if not os.path.isabs(filename) else filename
        page.screenshot(path=path, full_page=True)
        print(f"Screenshot saved: {path}")
        return path
    finally:
        browser.close()
        pw.stop()

def log_task(task_data, ratings, start_time):
    """记录完成的任务到日志"""
    entry = {
        "task_id": task_data.get("task_id", ""),
        "question": task_data.get("question", ""),
        "answer": task_data.get("answer", "")[:200],
        "ratings": ratings,
        "start_time": start_time,
        "end_time": datetime.now().isoformat(),
        "duration_seconds": (datetime.now() - datetime.fromisoformat(start_time)).total_seconds()
    }
    with open(TASK_LOG_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Task logged: {entry['task_id']} ({entry['duration_seconds']:.0f}s)")

def check_page_ready():
    """检查页面是否有新题目可做"""
    pw, browser, page = get_page()
    try:
        text = page.inner_text("body")
        has_task = "Task ID" in text and "Questions:" in text
        has_submit = bool(page.query_selector("button:has-text('Submit Rating')"))
        result = {
            "ready": has_task and has_submit,
            "has_task": has_task,
            "has_submit_button": has_submit,
            "url": page.url,
            "title": page.title()
        }
        print(json.dumps(result))
        return result
    finally:
        browser.close()
        pw.stop()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 browser_helper.py <command> [args]")
        print("Commands: read_task, fill_rating, submit, wait_and_submit, screenshot, check_page_ready")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "read_task":
        read_task()
    elif cmd == "fill_rating":
        if len(sys.argv) < 3:
            print("Usage: fill_rating '<json_string>'")
            sys.exit(1)
        fill_rating(sys.argv[2])
    elif cmd == "submit":
        submit()
    elif cmd == "wait_and_submit":
        start = sys.argv[2] if len(sys.argv) > 2 else None
        wait_and_submit(start)
    elif cmd == "screenshot":
        fn = sys.argv[2] if len(sys.argv) > 2 else None
        screenshot(fn)
    elif cmd == "check_page_ready":
        check_page_ready()
    elif cmd == "log_task":
        # Expects: log_task '<task_json>' '<ratings_json>' '<start_time_iso>'
        task_data = json.loads(sys.argv[2])
        ratings = json.loads(sys.argv[3])
        log_task(task_data, ratings, sys.argv[4])
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
