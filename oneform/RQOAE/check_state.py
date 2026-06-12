#!/usr/bin/env python3
import json, urllib.request
from websocket import create_connection

req = urllib.request.Request('http://browser:9223/json/list')
req.add_header('Host', 'localhost:9222')
p = json.loads(urllib.request.urlopen(req).read())[0]
ws = create_connection(p['webSocketDebuggerUrl'].replace('ws://localhost:9222', 'ws://browser:9223'))
mid = [0]

def send(method, params=None):
    mid[0] += 1
    m = mid[0]
    ws.send(json.dumps({'id': m, 'method': method, 'params': params or {}}))
    ws.settimeout(10)
    while True:
        r = ws.recv()
        d = json.loads(r)
        if d.get('id') == m:
            return d

def js(expr):
    r = send('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
    return r.get('result', {}).get('result', {}).get('value', '')

send('Runtime.enable')

print('URL:', js('window.location.href'))

# Modal info
modal_html = js("document.querySelector('.modal-container') ? document.querySelector('.modal-container').outerHTML : 'none'")
print('Modal HTML:', modal_html[:800])

# Slider states
for i in range(3):
    expr = (
        "(function(){"
        "var s=document.querySelectorAll('.rc-slider')[" + str(i) + "];"
        "if(!s) return 'no slider';"
        "var h=s.querySelector('.rc-slider-handle');"
        "var ad=s.querySelectorAll('.rc-slider-dot-active');"
        "return JSON.stringify({handle:!!h,style:h?h.getAttribute('style'):'',activeDots:ad.length});"
        "})()"
    )
    print(f'Slider {i}:', js(expr))

ws.close()
