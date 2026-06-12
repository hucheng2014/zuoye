#!/usr/bin/env python3
"""Set sliders, enable network monitoring, submit, and capture API response."""
import json, urllib.request, time, threading
from websocket import create_connection

CDP = 'http://browser:9223'
req = urllib.request.Request(f'{CDP}/json/list')
req.add_header('Host', 'localhost:9222')
pages = json.loads(urllib.request.urlopen(req, timeout=5).read())
ws_url = pages[0]['webSocketDebuggerUrl'].replace('ws://localhost:9222', 'ws://browser:9223')
ws = create_connection(ws_url, timeout=30, skip_utf8_validation=True)
mid = [0]
network_events = []

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

for domain in ['Runtime', 'DOM', 'Input', 'Network']:
    send(f'{domain}.enable')

# Close any modal
js("(function(){var m=document.querySelector('.modal-container');if(m){var b=m.querySelector('button');if(b)b.click();}return 'ok';})()")
time.sleep(0.5)

# Set all 3 sliders
ratings = [(0, 50, "Average"), (1, 50, "Average"), (2, 25, "Poor")]
for q_idx, pct, name in ratings:
    js("(function(){document.querySelectorAll('.rc-slider')[" + str(q_idx) + "].scrollIntoView({block:'center'});return 'ok';})()")
    time.sleep(0.8)
    rect = json.loads(js("(function(){var r=document.querySelectorAll('.rc-slider')[" + str(q_idx) + "].getBoundingClientRect();return JSON.stringify({l:r.left,t:r.top,w:r.width,h:r.height});})()"))
    cx = rect['l'] + rect['w'] * pct / 100
    cy = rect['t'] + rect['h'] / 2
    send('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': cx, 'y': cy})
    time.sleep(0.05)
    send('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1})
    time.sleep(0.05)
    send('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1})
    time.sleep(0.8)
    style = js("(function(){var s=document.querySelectorAll('.rc-slider')[" + str(q_idx) + "];var h=s.querySelector('.rc-slider-handle');return h?h.getAttribute('style'):'NOT SET';})()")
    print(f"Slider {q_idx} ({name}): {style}")

# Click second Submit Rating button
print("\nSubmitting...")
js("(function(){var btns=Array.from(document.querySelectorAll('button')).filter(function(b){return b.textContent.trim().includes('Submit Rating');});if(btns.length>=2)btns[1].click();else if(btns.length==1)btns[0].click();})()")

# Listen for network responses for 15 seconds
print("Listening for network events...")
ws.settimeout(1)
start = time.time()
responses = {}
while time.time() - start < 15:
    try:
        r = ws.recv()
        d = json.loads(r)
        method = d.get('method', '')
        params = d.get('params', {})
        
        if method == 'Network.requestWillBeSent':
            url = params.get('request', {}).get('url', '')
            req_id = params.get('requestId', '')
            if 'tryrating' in url or 'survey' in url or 'rating' in url.lower():
                print(f"  REQUEST: {params.get('request',{}).get('method','')} {url}")
                responses[req_id] = {'url': url, 'method': params.get('request',{}).get('method','')}
        
        elif method == 'Network.responseReceived':
            req_id = params.get('requestId', '')
            url = params.get('response', {}).get('url', '')
            status = params.get('response', {}).get('status', '')
            if 'tryrating' in url or req_id in responses:
                print(f"  RESPONSE: {status} {url}")
                if req_id in responses:
                    responses[req_id]['status'] = status
        
        elif method == 'Network.loadingFinished':
            req_id = params.get('requestId', '')
            if req_id in responses:
                # Get response body
                try:
                    body_resp = send('Network.getResponseBody', {'requestId': req_id})
                    body = body_resp.get('result', {}).get('body', '')
                    if body:
                        print(f"  BODY for {responses[req_id]['url']}: {body[:300]}")
                except:
                    pass
                    
    except Exception as e:
        if 'timed out' not in str(e).lower():
            pass

print("\nFinal URL:", js('window.location.href'))
print("Final body:", js('document.body.innerText.slice(0,400)'))
ws.close()
