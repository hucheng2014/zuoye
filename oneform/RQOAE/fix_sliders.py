"""Fix slider 1 (Average) and slider 2 (Awful) ratings"""
import json, urllib.request, time
from websocket import create_connection

CDP = 'http://browser:9223'
req = urllib.request.Request(f'{CDP}/json/list')
req.add_header('Host', 'localhost:9222')
pages = json.loads(urllib.request.urlopen(req, timeout=5).read())
ws_url = pages[0]['webSocketDebuggerUrl'].replace('ws://localhost:9222', 'ws://browser:9223')
ws = create_connection(ws_url, timeout=30, skip_utf8_validation=True)
mid = 0

def send(method, params=None):
    global mid
    mid += 1
    msg = {'id': mid, 'method': method}
    if params:
        msg['params'] = params
    ws.send(json.dumps(msg))
    ws.settimeout(10)
    while True:
        r = ws.recv()
        d = json.loads(r)
        if d.get('id') == mid:
            return d

def js(expr):
    r = send('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
    return r.get('result', {}).get('result', {}).get('value', '')

for domain in ['Runtime', 'DOM', 'Input']:
    send(f'{domain}.enable')

# slider 1 = intro -> Average (50%)
# slider 2 = outro -> Awful (0%)
tasks = [
    (1, 50, 'Average'),
    (2, 0,  'Awful'),
]

for slider_idx, pct, label in tasks:
    print(f'\n=== Slider {slider_idx}: {label} ({pct}%) ===')

    # Scroll into view
    scroll_js = 'document.querySelectorAll(".rc-slider")[IDX].scrollIntoView({block:"center",behavior:"smooth"})'.replace('IDX', str(slider_idx))
    js(scroll_js)
    time.sleep(1.5)

    # Get coordinates
    coord_js = (
        '(function(){'
        'var s=document.querySelectorAll(".rc-slider")[IDX];'
        'var r=s.getBoundingClientRect();'
        'var tx=r.left+(r.width*PCT/100);'
        'var ty=r.top+r.height/2;'
        'return JSON.stringify({x:tx,y:ty,top:r.top,left:r.left,w:r.width,h:r.height});'
        '})()'
    ).replace('IDX', str(slider_idx)).replace('PCT', str(pct))

    val = js(coord_js)
    if not val:
        print(f'  ERROR: no coords')
        continue

    c = json.loads(val)
    print(f'  rect: top={c["top"]:.0f}, left={c["left"]:.0f}, w={c["w"]:.0f}')
    print(f'  click at ({c["x"]:.1f}, {c["y"]:.1f})')

    send('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': c['x'], 'y': c['y']})
    time.sleep(0.1)
    send('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': c['x'], 'y': c['y'], 'button': 'left', 'clickCount': 1})
    time.sleep(0.1)
    send('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': c['x'], 'y': c['y'], 'button': 'left', 'clickCount': 1})
    time.sleep(1.0)

    # Verify
    verify_js = (
        '(function(){'
        'var s=document.querySelectorAll(".rc-slider")[IDX];'
        'var h=s.querySelector(".rc-slider-handle");'
        'var ad=s.querySelectorAll(".rc-slider-dot-active");'
        'return JSON.stringify({handle:!!h,activeDots:ad.length,style:h?h.getAttribute("style"):"none"});'
        '})()'
    ).replace('IDX', str(slider_idx))

    vval = js(verify_js)
    if vval:
        vd = json.loads(vval)
        print(f'  Result: handle={vd["handle"]}, activeDots={vd["activeDots"]}')
        print(f'  Style: {vd["style"]}')

    time.sleep(0.5)

ws.close()
print('\nDone')
