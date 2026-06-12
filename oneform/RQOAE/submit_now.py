"""Submit the current ratings"""
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

# Final check before submit
print('=== Pre-submit verification ===')
labels = ['bridge->Average', 'intro->Average', 'outro->Awful']
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
    print(f'  Slider {i} ({labels[i]}): activeDots={d["activeDots"]}, style={d["style"]} {"✓" if ok else "✗"}')

if not all_ok:
    print('ERROR: Not all sliders set. Aborting submit.')
    ws.close()
    exit(1)

print()
print('Clicking Submit Rating...')
result = js(
    '(function(){'
    'var btns=Array.from(document.querySelectorAll("button"));'
    'var submitBtn=btns.find(b=>b.textContent.trim()==="Submit Rating"&&!b.disabled);'
    'if(submitBtn){submitBtn.click();return "clicked: "+submitBtn.textContent.trim();}'
    'return "no Submit Rating button found. Buttons: "+btns.map(b=>b.textContent.trim()).join(", ");'
    '})()'
)
print(f'Submit result: {result}')
time.sleep(2.0)

# Check what happened
url = js('window.location.href')
print(f'URL after submit: {url}')

modal = js('document.querySelector(".modal-container")?.textContent?.trim()?.substring(0,200)')
print(f'Modal: {modal}')

btns = js('JSON.stringify(Array.from(document.querySelectorAll("button")).map(b=>b.textContent.trim()).filter(t=>t))')
print(f'Buttons: {btns}')

ws.close()
