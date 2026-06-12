"""Check all 3 sliders state and find what's blocking clicks"""
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

# Check all 3 sliders
for i in range(3):
    info = js(
        '(function(){'
        'var s=document.querySelectorAll(".rc-slider")[IDX];'
        'var r=s.getBoundingClientRect();'
        'var h=s.querySelector(".rc-slider-handle");'
        'var ad=s.querySelectorAll(".rc-slider-dot-active");'
        'return JSON.stringify({'
        '  top:Math.round(r.top),left:Math.round(r.left),w:Math.round(r.width),'
        '  handle:!!h,activeDots:ad.length,'
        '  style:h?h.getAttribute("style"):"none"'
        '});'
        '})()'
        .replace('IDX', str(i))
    )
    print(f'Slider {i}: {info}')

print()

# Check what element is at the click position for slider 1
# slider 1 is at top~487, left~742, w~938 -> 50% = x=1211, y=494
elem_at = js(
    '(function(){'
    'var e=document.elementFromPoint(1211, 494);'
    'return e ? e.tagName+"."+e.className.split(" ").join(".") : "null";'
    '})()'
)
print(f'Element at (1211, 494): {elem_at}')

# Check if there's a modal/overlay
overlay = js(
    'JSON.stringify(Array.from(document.querySelectorAll("[class*=modal],[class*=overlay],[class*=dialog]")).map(e=>({tag:e.tagName,cls:e.className,vis:e.style.display})))'
)
print(f'Overlays: {overlay}')

# Check z-index of slider 1
zidx = js(
    '(function(){'
    'var s=document.querySelectorAll(".rc-slider")[1];'
    'var e=s;var z=[];'
    'while(e){z.push(window.getComputedStyle(e).zIndex+"/"+e.tagName);e=e.parentElement;if(z.length>5)break;}'
    'return z.join(" > ");'
    '})()'
)
print(f'Slider 1 z-index chain: {zidx}')

# Try clicking via JS directly (not CDP mouse events)
print()
print('Trying JS click on slider 1 rail at 50%...')
result = js(
    '(function(){'
    'var s=document.querySelectorAll(".rc-slider")[1];'
    'var rail=s.querySelector(".rc-slider-rail");'
    'var r=rail.getBoundingClientRect();'
    'var x=r.left+r.width*0.5;'
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

# Check slider 1 state after JS click
info1 = js(
    '(function(){'
    'var s=document.querySelectorAll(".rc-slider")[1];'
    'var h=s.querySelector(".rc-slider-handle");'
    'var ad=s.querySelectorAll(".rc-slider-dot-active");'
    'return JSON.stringify({handle:!!h,activeDots:ad.length,style:h?h.getAttribute("style"):"none"});'
    '})()'
)
print(f'Slider 1 after JS click: {info1}')

ws.close()
