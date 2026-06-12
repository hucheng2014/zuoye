#!/usr/bin/env python3
"""Close any modal, set all 3 sliders correctly, then submit."""
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

# Step 1: Close any open modal
print("=== Step 1: Close modal if open ===")
modal_close = (
    "(function(){"
    "var m=document.querySelector('.modal-container');"
    "if(!m) return 'no modal';"
    "var btn=m.querySelector('button');"
    "if(btn){btn.click();return 'closed modal';}"
    "return 'no close button';"
    "})()"
)
print(js(modal_close))
time.sleep(0.5)

# Step 2: Set all 3 sliders
# Slider 0 (bridge #32): Average = 50%
# Slider 1 (intro #33): Average = 50%
# Slider 2 (outro #34): Poor = 25%
ratings = [(0, 50, "Average"), (1, 50, "Average"), (2, 25, "Poor")]

print("\n=== Step 2: Set sliders ===")
for q_idx, pct, name in ratings:
    print(f"\nSetting slider {q_idx} to {pct}% ({name})...")
    
    # Scroll into view
    scroll_js = (
        "(function(){"
        "document.querySelectorAll('.rc-slider')[" + str(q_idx) + "].scrollIntoView({block:'center'});"
        "return 'ok';"
        "})()"
    )
    js(scroll_js)
    time.sleep(0.8)
    
    # Get fresh rect
    rect_js = (
        "(function(){"
        "var r=document.querySelectorAll('.rc-slider')[" + str(q_idx) + "].getBoundingClientRect();"
        "return JSON.stringify({l:r.left,t:r.top,w:r.width,h:r.height});"
        "})()"
    )
    rect = json.loads(js(rect_js))
    cx = rect['l'] + rect['w'] * pct / 100
    cy = rect['t'] + rect['h'] / 2
    print(f"  Rect: {rect}, clicking at ({cx:.1f}, {cy:.1f})")
    
    send('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': cx, 'y': cy})
    time.sleep(0.05)
    send('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1})
    time.sleep(0.05)
    send('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1})
    time.sleep(0.8)
    
    # Verify
    verify_js = (
        "(function(){"
        "var s=document.querySelectorAll('.rc-slider')[" + str(q_idx) + "];"
        "var h=s.querySelector('.rc-slider-handle');"
        "var ad=s.querySelectorAll('.rc-slider-dot-active');"
        "return JSON.stringify({handle:!!h,style:h?h.getAttribute('style'):'',activeDots:ad.length});"
        "})()"
    )
    v = json.loads(js(verify_js))
    print(f"  Result: handle={v['handle']}, activeDots={v['activeDots']}, style={v['style']}")
    if not v['handle']:
        print("  ERROR: Slider not set!")

# Step 3: Final check
print("\n=== Step 3: Final state ===")
all_ok = True
for i in range(3):
    check = (
        "(function(){"
        "var s=document.querySelectorAll('.rc-slider')[" + str(i) + "];"
        "var h=s.querySelector('.rc-slider-handle');"
        "var ad=s.querySelectorAll('.rc-slider-dot-active');"
        "return JSON.stringify({handle:!!h,style:h?h.getAttribute('style'):'',activeDots:ad.length});"
        "})()"
    )
    v = json.loads(js(check))
    print(f"  Slider {i}: handle={v['handle']}, activeDots={v['activeDots']}, style={v['style']}")
    if not v['handle']:
        all_ok = False

if all_ok:
    print("\n=== Step 4: Submit ===")
    submit_js = (
        "(function(){"
        "var btns=Array.from(document.querySelectorAll('button'));"
        "var btn=btns.find(function(b){return b.textContent.trim().includes('Submit Rating');});"
        "if(btn){btn.click();return 'clicked: '+btn.textContent.trim();}"
        "return 'Submit button not found';"
        "})()"
    )
    print(js(submit_js))
    time.sleep(3)
    
    # Check result
    modal_text = js("document.querySelector('.modal-container') ? document.querySelector('.modal-container').innerText : 'no modal'")
    print('Modal after submit:', modal_text)
    print('URL:', js('window.location.href'))
else:
    print("\nERROR: Not all sliders set, skipping submit!")

ws.close()
print("\nDone!")
