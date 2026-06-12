"""
Generic page handler: set all 3 sliders and submit.
Pass ratings as: python3 do_page.py 2 2 2
(0=Awful, 1=Poor, 2=Average, 3=Good, 4=Excellent)
"""
import json, sys, urllib.request, time
from websocket import create_connection

# Parse args
if len(sys.argv) != 4:
    print("Usage: do_page.py <dot0> <dot1> <dot2>")
    print("  dot: 0=Awful, 1=Poor, 2=Average, 3=Good, 4=Excellent")
    sys.exit(1)

dots = [int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])]
fracs = [0.0, 0.25, 0.5, 0.75, 1.0]
labels = ['Awful', 'Poor', 'Average', 'Good', 'Excellent']
expected_active = [1, 2, 3, 4, 5]  # active dots count for each rating

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

for domain in ['Runtime', 'Input']:
    send(f'{domain}.enable')

def scroll_to(slider_idx):
    js(
        '(function(){'
        'var container=document.querySelector(".application-wrapper--content");'
        'var slider=document.querySelectorAll(".rc-slider")[IDX];'
        'var el=slider;var top=0;'
        'while(el&&el!==container){top+=el.offsetTop;el=el.offsetParent;}'
        'container.scrollTop=top-container.clientHeight/2+slider.offsetHeight/2;'
        '})()'
        .replace('IDX', str(slider_idx))
    )

def cdp_click(x, y):
    send('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': x, 'y': y})
    time.sleep(0.05)
    send('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})
    time.sleep(0.05)
    send('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})

def get_coords(slider_idx, frac):
    val = js(
        '(function(){'
        'var s=document.querySelectorAll(".rc-slider")[IDX];'
        'var r=s.querySelector(".rc-slider-rail").getBoundingClientRect();'
        'return JSON.stringify({x:r.left+r.width*FRAC,y:r.top+r.height/2,top:r.top});'
        '})()'
        .replace('IDX', str(slider_idx))
        .replace('FRAC', str(frac))
    )
    return json.loads(val) if val else None

def get_state(slider_idx):
    d = js('document.querySelectorAll(".rc-slider")[IDX].querySelectorAll(".rc-slider-dot-active").length'.replace('IDX', str(slider_idx)))
    s = js('document.querySelectorAll(".rc-slider")[IDX].querySelector(".rc-slider-handle")?.getAttribute("style")'.replace('IDX', str(slider_idx)))
    return d, s

print('=== Setting sliders ===')
for i, dot in enumerate(dots):
    frac = fracs[dot]
    label = labels[dot]
    exp = expected_active[dot]
    print(f'\n  Slider {i} -> {label} ({int(frac*100)}%)')

    scroll_to(i)
    time.sleep(1.0)

    coords = get_coords(i, frac)
    if not coords:
        print(f'  ERROR: no coords')
        continue

    top = coords['top']
    print(f'  Rail top={top:.0f}, click at ({coords["x"]:.1f}, {coords["y"]:.1f})')

    cdp_click(coords['x'], coords['y'])
    time.sleep(1.0)

    d, s = get_state(i)
    ok = str(d) == str(exp)
    print(f'  Result: activeDots={d} {"✓" if ok else "✗"}')
    if s:
        print(f'  Style: {s}')

print()
print('=== Final verification ===')
all_ok = True
for i, dot in enumerate(dots):
    exp = expected_active[dot]
    d, s = get_state(i)
    ok = str(d) == str(exp)
    if not ok:
        all_ok = False
    print(f'  Slider {i} ({labels[dot]}): activeDots={d} {"✓" if ok else "✗"}')

print()
if not all_ok:
    print('ERROR: Not all sliders set. Aborting submit.')
    ws.close()
    sys.exit(1)

print('All sliders set correctly!')
print()
print('=== Submitting ===')
submit = js(
    '(function(){'
    'var btns=Array.from(document.querySelectorAll("button"));'
    'var btn=btns.find(b=>b.textContent.trim()==="Submit Rating"&&!b.disabled);'
    'if(btn){btn.click();return "clicked: "+btn.textContent.trim();}'
    'return "not found. buttons: "+btns.map(b=>b.textContent.trim()).join("|");'
    '})()'
)
print(f'Submit: {submit}')
time.sleep(3.0)

url = js('window.location.href')
print(f'URL: {url}')
modal = js('document.querySelector(".modal-container")?.textContent?.trim()?.substring(0,200)')
print(f'Modal: {modal!r}')
btns = js('JSON.stringify(Array.from(document.querySelectorAll("button")).map(b=>b.textContent.trim()).filter(t=>t))')
print(f'Buttons: {btns}')

ws.close()
