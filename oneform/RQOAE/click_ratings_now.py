"""
当前页面评分：
  slider 0 (bridge 4.4-9.2s): Average → dot 2 (50%)
  slider 1 (intro 0-7s):       Average → dot 2 (50%)
  slider 2 (outro 15.2-17.2s): Awful   → dot 0 (0%)
"""
import json, urllib.request, time
from websocket import create_connection

CDP = 'http://browser:9223'
req = urllib.request.Request(f'{CDP}/json/list')
req.add_header('Host', 'localhost:9222')
resp = urllib.request.urlopen(req, timeout=5)
pages = json.loads(resp.read())
ws_url = pages[0]['webSocketDebuggerUrl'].replace('ws://localhost:9222', 'ws://browser:9223')

ws = create_connection(ws_url, timeout=30, skip_utf8_validation=True)
msg_id = 0

def send_and_recv(method, params=None):
    global msg_id
    msg_id += 1
    msg = {'id': msg_id, 'method': method}
    if params:
        msg['params'] = params
    ws.send(json.dumps(msg))
    ws.settimeout(15)
    while True:
        r = ws.recv()
        d = json.loads(r)
        if d.get('id') == msg_id:
            return d

def eval_js(js):
    result = send_and_recv('Runtime.evaluate', {'expression': js, 'returnByValue': True})
    return result.get('result', {}).get('result', {}).get('value', '')

for domain in ['Runtime', 'DOM', 'Input']:
    send_and_recv(f'{domain}.enable')

# Verify audio sources (these are the 3 formal questions at index 32-34)
print("=== Verifying audio sources ===")
for i in range(3):
    src = eval_js(f'document.querySelectorAll("audio")[{32+i}].src')
    fname = src.split("fileName=")[-1] if src else "N/A"
    print(f"  Audio {32+i}: {fname}")

print()

# dot index: 0=Awful(0%), 1=Poor(25%), 2=Average(50%), 3=Good(75%), 4=Excellent(100%)
# pct:       0%           25%          50%              75%           100%
ratings = [
    (0, 2, 'Average'),   # slider 0 = bridge
    (1, 2, 'Average'),   # slider 1 = intro
    (2, 0, 'Awful'),     # slider 2 = outro (silence_ratio=0.622 > 0.5)
]
pcts = [0, 25, 50, 75, 100]

# Count total sliders to find the right ones
total_sliders = eval_js('document.querySelectorAll(".rc-slider").length')
print(f"Total sliders on page: {total_sliders}")

# The formal questions are the last 3 sliders
# Determine offset: if 35 sliders total, formal ones are at index 32,33,34
slider_offset = int(total_sliders) - 3 if total_sliders else 32

for q_idx, dot_idx, label in ratings:
    slider_idx = slider_offset + q_idx
    pct = pcts[dot_idx]
    print(f"\n=== Slider {slider_idx} (question {q_idx}): '{label}' (dot {dot_idx}, {pct}%) ===")

    # Scroll into view
    eval_js(f'(function(){{var s=document.querySelectorAll(".rc-slider")[{slider_idx}];s.scrollIntoView({{block:"center"}});return "ok"}})()')
    time.sleep(1.0)

    # Get coordinates
    coord_js = (
        f'(function(){{'
        f'var s=document.querySelectorAll(".rc-slider")[{slider_idx}];'
        f'var r=s.getBoundingClientRect();'
        f'var tx=r.left+(r.width*{pct}/100);'
        f'var ty=r.top+r.height/2;'
        f'return JSON.stringify({{x:tx,y:ty,l:r.left,t:r.top,w:r.width,h:r.height}})'
        f'}})()'
    )
    val = eval_js(coord_js)
    if not val:
        print(f"  ERROR: Could not get coordinates for slider {slider_idx}")
        continue

    coords = json.loads(val)
    cx, cy = coords['x'], coords['y']
    print(f"  Slider rect: left={coords['l']:.0f}, top={coords['t']:.0f}, w={coords['w']:.0f}, h={coords['h']:.0f}")
    print(f"  Clicking at ({cx:.1f}, {cy:.1f})")

    send_and_recv('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': cx, 'y': cy})
    time.sleep(0.05)
    send_and_recv('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1})
    time.sleep(0.05)
    send_and_recv('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1})
    time.sleep(1.0)

    # Verify
    verify_js = (
        f'(function(){{'
        f'var s=document.querySelectorAll(".rc-slider")[{slider_idx}];'
        f'var h=s.querySelector(".rc-slider-handle");'
        f'var ad=s.querySelectorAll(".rc-slider-dot-active");'
        f'return JSON.stringify({{handle:!!h,style:h?h.getAttribute("style"):"",activeDots:ad.length}})'
        f'}})()'
    )
    vval = eval_js(verify_js)
    if vval:
        vd = json.loads(vval)
        print(f"  Verify: handle={vd['handle']}, activeDots={vd['activeDots']}, style={vd['style']}")

    time.sleep(0.5)

ws.close()
print("\nAll ratings set. Ready for Submit.")
