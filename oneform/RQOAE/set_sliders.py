#!/usr/bin/env python3
"""Set sliders and submit. Ratings: slider1=Average(50%), slider2=Poor(25%)"""
import json, urllib.request, time
from websocket import create_connection

CDP = 'http://browser:9223'
req = urllib.request.Request(f'{CDP}/json/list')
req.add_header('Host', 'localhost:9222')
pages = json.loads(urllib.request.urlopen(req, timeout=5).read())
ws_url = pages[0]['webSocketDebuggerUrl'].replace('ws://localhost:9222', 'ws://browser:9223')
ws = create_connection(ws_url, timeout=30, skip_utf8_validation=True)
mid = [0]

def send(method, params=None):
    mid[0] += 1
    m = mid[0]
    ws.send(json.dumps({'id': m, 'method': method, 'params': params or {}}))
    ws.settimeout(15)
    while True:
        r = ws.recv()
        d = json.loads(r)
        if d.get('id') == m:
            return d

def js(expr):
    r = send('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
    return r.get('result', {}).get('result', {}).get('value', '')

for domain in ['Runtime', 'DOM', 'Input']:
    send(f'{domain}.enable')

# Verify current state of all sliders
print("=== Current slider state ===")
for i in range(3):
    check = (
        "(function(){"
        "var s=document.querySelectorAll('.rc-slider')[" + str(i) + "];"
        "var h=s.querySelector('.rc-slider-handle');"
        "var ad=s.querySelectorAll('.rc-slider-dot-active');"
        "return JSON.stringify({handle:!!h,style:h?h.getAttribute('style'):'',activeDots:ad.length});"
        "})()"
    )
    print(f"  Slider {i}: {js(check)}")

# Ratings to set: {slider_index: percentage}
# Slider 0 (bridge #32): already set to 50% (Average) - skip
# Slider 1 (intro #33): Average = 50%
# Slider 2 (outro #34): Poor = 25%
to_set = [(1, 50, "Average"), (2, 25, "Poor")]

for q_idx, pct, name in to_set:
    print(f"\n=== Setting slider {q_idx} to {pct}% ({name}) ===")
    
    # Scroll into view
    scroll_js = (
        "(function(){"
        "document.querySelectorAll('.rc-slider')[" + str(q_idx) + "].scrollIntoView({block:'center'});"
        "return 'ok';"
        "})()"
    )
    js(scroll_js)
    time.sleep(1.0)
    
    # Get fresh rect after scroll
    rect_js = (
        "(function(){"
        "var r=document.querySelectorAll('.rc-slider')[" + str(q_idx) + "].getBoundingClientRect();"
        "return JSON.stringify({l:r.left,t:r.top,w:r.width,h:r.height});"
        "})()"
    )
    rect_str = js(rect_js)
    print(f"  Rect: {rect_str}")
    rect = json.loads(rect_str)
    
    cx = rect['l'] + rect['w'] * pct / 100
    cy = rect['t'] + rect['h'] / 2
    print(f"  Clicking at ({cx:.1f}, {cy:.1f})")
    
    send('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': cx, 'y': cy})
    time.sleep(0.05)
    send('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1})
    time.sleep(0.05)
    send('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1})
    time.sleep(1.0)
    
    # Verify
    verify_js = (
        "(function(){"
        "var s=document.querySelectorAll('.rc-slider')[" + str(q_idx) + "];"
        "var h=s.querySelector('.rc-slider-handle');"
        "var ad=s.querySelectorAll('.rc-slider-dot-active');"
        "return JSON.stringify({handle:!!h,style:h?h.getAttribute('style'):'',activeDots:ad.length});"
        "})()"
    )
    v = js(verify_js)
    print(f"  Verify: {v}")
    vd = json.loads(v)
    if not vd['handle']:
        print("  WARNING: Click did not register! Trying dot.click() fallback...")
        dot_idx = pct // 25  # 0%=0, 25%=1, 50%=2, 75%=3, 100%=4
        dot_js = (
            "(function(){"
            "var s=document.querySelectorAll('.rc-slider')[" + str(q_idx) + "];"
            "var dots=s.querySelectorAll('.rc-slider-dot');"
            "if(dots[" + str(dot_idx) + "]){dots[" + str(dot_idx) + "].click();return 'clicked dot " + str(dot_idx) + "';}"
            "return 'dot not found';"
            "})()"
        )
        print(f"  Dot click result: {js(dot_js)}")
        time.sleep(0.5)
        print(f"  Re-verify: {js(verify_js)}")

print("\n=== Final slider state ===")
for i in range(3):
    check = (
        "(function(){"
        "var s=document.querySelectorAll('.rc-slider')[" + str(i) + "];"
        "var h=s.querySelector('.rc-slider-handle');"
        "var ad=s.querySelectorAll('.rc-slider-dot-active');"
        "return JSON.stringify({handle:!!h,style:h?h.getAttribute('style'):'',activeDots:ad.length});"
        "})()"
    )
    print(f"  Slider {i}: {js(check)}")

print("\nAll sliders set. Ready to submit.")
ws.close()
