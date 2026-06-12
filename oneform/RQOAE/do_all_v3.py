"""
Set all 3 sliders and submit.
Handles scroll container properly.
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

def scroll_to_slider(slider_idx):
    """Scroll the scroll container so the slider is in viewport center"""
    js(
        '(function(){'
        'var s=document.querySelectorAll(".rc-slider")[IDX];'
        # Find scroll container
        'var container=s.parentElement;'
        'while(container){'
        '  var style=window.getComputedStyle(container);'
        '  if(style.overflow==="auto"||style.overflow==="scroll"||style.overflowY==="auto"||style.overflowY==="scroll") break;'
        '  container=container.parentElement;'
        '}'
        'if(!container){s.scrollIntoView({block:"center"});return;}'
        # Scroll container so slider is centered
        'var containerRect=container.getBoundingClientRect();'
        'var sliderRect=s.getBoundingClientRect();'
        'var offset=sliderRect.top-containerRect.top+container.scrollTop-containerRect.height/2+sliderRect.height/2;'
        'container.scrollTop=offset;'
        '})()'
        .replace('IDX', str(slider_idx))
    )

def click_slider(slider_idx, frac):
    """Click slider rail at given fraction using click event"""
    return js(
        '(function(){'
        'var s=document.querySelectorAll(".rc-slider")[IDX];'
        'var rail=s.querySelector(".rc-slider-rail");'
        'var r=rail.getBoundingClientRect();'
        'var x=r.left+r.width*FRAC;'
        'var y=r.top+r.height/2;'
        'var e=new MouseEvent("click",{bubbles:true,cancelable:true,clientX:x,clientY:y});'
        'rail.dispatchEvent(e);'
        'return "ok at "+Math.round(x)+","+Math.round(y)+" (top="+Math.round(r.top)+")";'
        '})()'
        .replace('IDX', str(slider_idx))
        .replace('FRAC', str(frac))
    )

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
    scroll_to_slider(slider_idx)
    time.sleep(1.0)
    
    # Check position after scroll
    top = js('Math.round(document.querySelectorAll(".rc-slider")[IDX].getBoundingClientRect().top)'.replace('IDX', str(slider_idx)))
    print(f'  Slider {slider_idx} top after scroll: {top}')
    
    result = click_slider(slider_idx, frac)
    time.sleep(0.8)
    
    dots, style = get_state(slider_idx)
    ok = str(dots) == expected
    print(f'  Slider {slider_idx} ({label}): {result} -> activeDots={dots} {"✓" if ok else "✗"}')
    if style:
        print(f'    style: {style}')

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
    print('ERROR: Not all sliders set. Aborting submit.')
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
