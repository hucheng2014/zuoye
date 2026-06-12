"""
Complete workflow:
1. Close modal if open
2. Set all 3 sliders
3. Submit
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

send('Runtime.enable')

# Step 1: Close modal
print('Step 1: Close modal')
modal_text = js('document.querySelector(".modal-container")?.textContent?.trim()?.substring(0,50)')
print(f'  Modal: {modal_text!r}')
if modal_text:
    close = js(
        '(function(){'
        'var modal=document.querySelector(".modal-container");'
        'var btn=modal?.querySelector("button");'
        'if(btn){btn.click();return "closed";}return "no button";'
        '})()'
    )
    print(f'  Close: {close}')
    time.sleep(1.0)
    modal_text2 = js('document.querySelector(".modal-container")?.textContent?.trim()?.substring(0,50)')
    print(f'  Modal after: {modal_text2!r}')

print()

# Step 2: Set all 3 sliders
print('Step 2: Set sliders')
tasks = [
    (0, 0.5, 'Average', 3),   # bridge -> 50% -> 3 active dots
    (1, 0.5, 'Average', 3),   # intro  -> 50% -> 3 active dots
    (2, 0.0, 'Awful',   1),   # outro  -> 0%  -> 1 active dot
]

for slider_idx, frac, label, expected_dots in tasks:
    print(f'  Slider {slider_idx} -> {label} ({int(frac*100)}%)')
    result = js(
        '(function(){'
        'var s=document.querySelectorAll(".rc-slider")[IDX];'
        'var rail=s.querySelector(".rc-slider-rail");'
        'var r=rail.getBoundingClientRect();'
        'var x=r.left+r.width*FRAC;'
        'var y=r.top+r.height/2;'
        'var opts={bubbles:true,cancelable:true,clientX:x,clientY:y};'
        'rail.dispatchEvent(new MouseEvent("mousedown",opts));'
        'rail.dispatchEvent(new MouseEvent("mouseup",opts));'
        'rail.dispatchEvent(new MouseEvent("click",opts));'
        'return "ok at "+Math.round(x)+","+Math.round(y);'
        '})()'
        .replace('IDX', str(slider_idx))
        .replace('FRAC', str(frac))
    )
    time.sleep(0.8)
    
    dots = js('document.querySelectorAll(".rc-slider")[IDX].querySelectorAll(".rc-slider-dot-active").length'.replace('IDX', str(slider_idx)))
    style = js('document.querySelectorAll(".rc-slider")[IDX].querySelector(".rc-slider-handle")?.getAttribute("style")'.replace('IDX', str(slider_idx)))
    ok = str(dots) == str(expected_dots)
    print(f'    activeDots={dots}, style={style!r} {"✓" if ok else "✗ WRONG"}')

print()

# Step 3: Final check
print('Step 3: Final verification')
all_ok = True
for i, (_, _, label, expected) in enumerate(tasks):
    dots = js('document.querySelectorAll(".rc-slider")[IDX].querySelectorAll(".rc-slider-dot-active").length'.replace('IDX', str(i)))
    style = js('document.querySelectorAll(".rc-slider")[IDX].querySelector(".rc-slider-handle")?.getAttribute("style")'.replace('IDX', str(i)))
    ok = str(dots) == str(expected)
    if not ok:
        all_ok = False
    print(f'  Slider {i} ({label}): activeDots={dots} {"✓" if ok else "✗"}')

print()
if not all_ok:
    print('ERROR: Sliders not set correctly. Aborting.')
    ws.close()
    exit(1)

# Step 4: Submit
print('Step 4: Submitting...')
submit = js(
    '(function(){'
    'var btns=Array.from(document.querySelectorAll("button"));'
    'var btn=btns.find(b=>b.textContent.trim()==="Submit Rating"&&!b.disabled);'
    'if(btn){btn.click();return "clicked Submit Rating";}'
    'return "not found. buttons: "+btns.map(b=>b.textContent.trim()).join("|");'
    '})()'
)
print(f'  Submit: {submit}')
time.sleep(3.0)

# Check result
url = js('window.location.href')
print(f'  URL: {url}')
modal = js('document.querySelector(".modal-container")?.textContent?.trim()?.substring(0,200)')
print(f'  Modal: {modal!r}')
btns = js('JSON.stringify(Array.from(document.querySelectorAll("button")).map(b=>b.textContent.trim()).filter(t=>t))')
print(f'  Buttons: {btns}')

ws.close()
