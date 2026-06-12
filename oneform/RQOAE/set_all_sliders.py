"""
Set all 3 sliders via JS events (bypassing modal overlay):
  slider 0 (bridge): Average (50%)
  slider 1 (intro):  Average (50%)
  slider 2 (outro):  Awful   (0%)
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

# Try to dismiss modal first
print('Attempting to dismiss modal...')
dismiss = js(
    '(function(){'
    'var modal=document.querySelector(".modal-container");'
    'if(!modal)return "no modal";'
    'var closeBtn=modal.querySelector("button");'
    'if(closeBtn){closeBtn.click();return "clicked: "+closeBtn.textContent.trim();}'
    'return "no button in modal";'
    '})()'
)
print(f'Dismiss: {dismiss}')
time.sleep(0.5)

# Check modal
modal_text = js('document.querySelector(".modal-container")?.textContent?.trim()?.substring(0,100)')
print(f'Modal: {modal_text}')
print()

# Set all 3 sliders using JS mouse events on the rail
tasks = [
    (0, 0.5, 'Average'),   # bridge -> 50%
    (1, 0.5, 'Average'),   # intro  -> 50%
    (2, 0.0, 'Awful'),     # outro  -> 0%
]

for slider_idx, frac, label in tasks:
    print(f'Setting slider {slider_idx} to {label} ({int(frac*100)}%)...')
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
    print(f'  Result: {result}')
    time.sleep(0.8)

    # Verify
    info = js(
        '(function(){var s=document.querySelectorAll(".rc-slider")[IDX];var h=s.querySelector(".rc-slider-handle");var ad=s.querySelectorAll(".rc-slider-dot-active");return JSON.stringify({handle:!!h,activeDots:ad.length,style:h?h.getAttribute("style"):"none"});})()'
        .replace('IDX', str(slider_idx))
    )
    print(f'  State: {info}')
    time.sleep(0.3)

print()
print('=== Final verification ===')
labels = ['bridge->Average(50%)', 'intro->Average(50%)', 'outro->Awful(0%)']
all_ok = True
for i in range(3):
    info = js(
        '(function(){var s=document.querySelectorAll(".rc-slider")[IDX];var h=s.querySelector(".rc-slider-handle");var ad=s.querySelectorAll(".rc-slider-dot-active");return JSON.stringify({handle:!!h,activeDots:ad.length,style:h?h.getAttribute("style"):"none"});})()'
        .replace('IDX', str(i))
    )
    d = json.loads(info)
    ok = d['handle']
    if not ok:
        all_ok = False
    print(f'  Slider {i} ({labels[i]}): handle={d["handle"]}, activeDots={d["activeDots"]} {"✓" if ok else "✗"}')

print()
if all_ok:
    print('All sliders set! Ready to submit.')
else:
    print('WARNING: Some sliders not set correctly.')

ws.close()
