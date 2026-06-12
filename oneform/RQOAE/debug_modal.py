#!/usr/bin/env python3
import json, urllib.request, time
from websocket import create_connection

CDP = 'http://browser:9223'
req = urllib.request.Request(f'{CDP}/json/list')
req.add_header('Host', 'localhost:9222')
pages = json.loads(urllib.request.urlopen(req, timeout=5).read())
ws_url = pages[0]['webSocketDebuggerUrl'].replace('ws://localhost:9222', 'ws://browser:9223')
ws = create_connection(ws_url, timeout=30, skip_utf8_validation=True)
mid = [0]

def send(method, params=None):
    mid[0] += 1
    m = mid[0]
    ws.send(json.dumps({'id': m, 'method': method, 'params': params or {}}))
    ws.settimeout(15)
    while True:
        r = ws.recv()
        d = json.loads(r)
        if d.get('id') == m:
            return d

def js(expr):
    r = send('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
    return r.get('result', {}).get('result', {}).get('value', '')

send('Runtime.enable')

# Full modal HTML
print("Modal full HTML:")
print(js("document.querySelector('.modal-container') ? document.querySelector('.modal-container').outerHTML : 'none'"))

print("\nModal class:", js("document.querySelector('.modal-container') ? document.querySelector('.modal-container').className : 'none'"))
print("Modal visible:", js("document.querySelector('.modal-container.visible') ? 'yes' : 'no'"))

# Check all buttons on page
print("\nAll buttons:")
print(js("JSON.stringify(Array.from(document.querySelectorAll('button')).map(function(b){return {text:b.textContent.trim().slice(0,50),disabled:b.disabled,class:b.className.slice(0,50)};}))"))

# Check page body text
print("\nPage body text (first 600 chars):")
print(js("document.body.innerText.slice(0,600)"))

ws.close()
