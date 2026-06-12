"""
Set all 3 sliders and submit.
- Scroll main container to bring each slider into viewport
- Use CDP mouse events to click
"""
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

for domain in ['Runtime', 'Input']:
    send(f'{domain}.enable')

def scroll_slider_into_view(slider_idx):
    """Scroll main container to center the slider in viewport"""
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

def get_rail_coords(slider_idx, frac):
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
    dots = js('document.querySelectorAll(".rc-slider")[IDX].querySelectorAll(".rc-slider-dot-active").length'.replace('IDX', str(slider_idx)))
    style = js('document.querySelectorAll(".rc-slider")[IDX].querySelector(".rc-slider-handle")?.getAttribute("style")'.replace('IDX', str(slider_idx)))
    return dots, style

# Tasks: (slider_idx, fraction, label, expected_active_dots)
tasks = [
    (0, 0.5, 'Average', '3'),   # bridge -> 50%
    (1, 0.5, 'Average', '3'),   # intro  -> 50%
    (2, 0.0, 'Awful',   '1'),   # outro  -> 0%
]

print('=== Setting sliders ===')
for slider_idx, frac, label, expected in tasks:
    print(f'\n  Slider {slider_idx} -> {label} ({int(frac*100)}%)')
    
    # Scroll into view
    scroll_slider_into_view(slider_idx)
    time.sleep(1.0)
    
    # Get coords
    coords = get_rail_coords(slider_idx, frac)
    if not coords:
        print(f'  ERROR: no coords')
        continue
    
    top = coords['top']
    print(f'  Rail top={top:.0f}, click at ({coords["x"]:.1f}, {coords["y"]:.1f})')
    
    if top < 0 or top > 900:
        print(f'  WARNING: slider not in viewport (top={top:.0f}), trying again...')
        scroll_slider_into_view(slider_idx)
        time.sleep(1.0)
        coords = get_rail_coords(slider_idx, frac)
        if coords:
            top = coords['top']
            print(f'  After re-scroll: top={top:.0f}')
    
    # CDP click
    cdp_click(coords['x'], coords['y'])
    time.sleep(1.0)
    
    dots, style = get_state(slider_idx)
    ok = str(dots) == expected
    print(f'  Result: activeDots={dots} {"✓" if ok else "✗"}')
    if style:
        print(f'  Style: {style}')

print()
print('=== Final verification ===')
all_ok = True
for slider_idx, _, label, expected in tasks:
    dots, style = get_state(slider_idx)
    ok = str(dots) == expected
    if not ok:
        all_ok = False
    print(f'  Slider {slider_idx} ({label}): activeDots={dots} {"✓" if ok else "✗"}')

print()
if not all_ok:
    print('ERROR: Not all sliders set correctly. Aborting submit.')
    ws.close()
    exit(1)

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
modal = js('document.querySelector(".modal-container")?.textContent?.trim()?.substring(0,300)')
print(f'Modal: {modal!r}')
btns = js('JSON.stringify(Array.from(document.querySelectorAll("button")).map(b=>b.textContent.trim()).filter(t=>t))')
print(f'Buttons: {btns}')

ws.close()
