"""Set slider 2 to Awful (0%) via JS events, bypassing modal overlay"""
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

# Check current state of all 3 sliders
print('=== Current slider states ===')
for i in range(3):
    info = js(
        '(function(){var s=document.querySelectorAll(".rc-slider")[IDX];var h=s.querySelector(".rc-slider-handle");var ad=s.querySelectorAll(".rc-slider-dot-active");return JSON.stringify({handle:!!h,activeDots:ad.length,style:h?h.getAttribute("style"):"none"});})()'
        .replace('IDX', str(i))
    )
    print(f'  Slider {i}: {info}')

print()

# Set slider 2 to Awful (0%) via JS mouse events on the rail
print('Setting slider 2 to Awful (0%)...')
result = js(
    '(function(){'
    'var s=document.querySelectorAll(".rc-slider")[2];'
    'var rail=s.querySelector(".rc-slider-rail");'
    'var r=rail.getBoundingClientRect();'
    'var x=r.left;'  # 0% = leftmost
    'var y=r.top+r.height/2;'
    'var evt=new MouseEvent("mousedown",{bubbles:true,cancelable:true,clientX:x,clientY:y});'
    'rail.dispatchEvent(evt);'
    'var evt2=new MouseEvent("mouseup",{bubbles:true,cancelable:true,clientX:x,clientY:y});'
    'rail.dispatchEvent(evt2);'
    'var evt3=new MouseEvent("click",{bubbles:true,cancelable:true,clientX:x,clientY:y});'
    'rail.dispatchEvent(evt3);'
    'return "dispatched at "+Math.round(x)+","+Math.round(y);'
    '})()'
)
print(f'JS click result: {result}')
time.sleep(1.0)

# Verify
info2 = js(
    '(function(){var s=document.querySelectorAll(".rc-slider")[2];var h=s.querySelector(".rc-slider-handle");var ad=s.querySelectorAll(".rc-slider-dot-active");return JSON.stringify({handle:!!h,activeDots:ad.length,style:h?h.getAttribute("style"):"none"});})()'
)
print(f'Slider 2 after: {info2}')

# Also verify slider 0 and 1 are still set
print()
print('=== Final states ===')
labels = ['bridge->Average', 'intro->Average', 'outro->Awful']
for i in range(3):
    info = js(
        '(function(){var s=document.querySelectorAll(".rc-slider")[IDX];var h=s.querySelector(".rc-slider-handle");var ad=s.querySelectorAll(".rc-slider-dot-active");return JSON.stringify({handle:!!h,activeDots:ad.length,style:h?h.getAttribute("style"):"none"});})()'
        .replace('IDX', str(i))
    )
    print(f'  Slider {i} ({labels[i]}): {info}')

ws.close()
print('\nDone - ready to submit')
