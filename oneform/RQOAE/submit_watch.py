#!/usr/bin/env python3
"""Set sliders, submit, and watch for modal content."""
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

for domain in ['Runtime', 'DOM', 'Input']:
    send(f'{domain}.enable')

# Close any modal first
js("(function(){var m=document.querySelector('.modal-container');if(m){var b=m.querySelector('button');if(b)b.click();}return 'ok';})()")
time.sleep(0.5)

# Set all 3 sliders
ratings = [(0, 50, "Average"), (1, 50, "Average"), (2, 25, "Poor")]
for q_idx, pct, name in ratings:
    scroll_js = "(function(){document.querySelectorAll('.rc-slider')[" + str(q_idx) + "].scrollIntoView({block:'center'});return 'ok';})()"
    js(scroll_js)
    time.sleep(0.8)
    rect_js = "(function(){var r=document.querySelectorAll('.rc-slider')[" + str(q_idx) + "].getBoundingClientRect();return JSON.stringify({l:r.left,t:r.top,w:r.width,h:r.height});})()"
    rect = json.loads(js(rect_js))
    cx = rect['l'] + rect['w'] * pct / 100
    cy = rect['t'] + rect['h'] / 2
    send('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': cx, 'y': cy})
    time.sleep(0.05)
    send('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1})
    time.sleep(0.05)
    send('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1})
    time.sleep(0.8)
    verify_js = "(function(){var s=document.querySelectorAll('.rc-slider')[" + str(q_idx) + "];var h=s.querySelector('.rc-slider-handle');return h?h.getAttribute('style'):'NOT SET';})()"
    print(f"Slider {q_idx} ({name}): {js(verify_js)}")

# Check all buttons and their positions
print("\nAll Submit buttons:")
btns_info = js("JSON.stringify(Array.from(document.querySelectorAll('button')).filter(function(b){return b.textContent.trim().includes('Submit');}).map(function(b){var r=b.getBoundingClientRect();return {text:b.textContent.trim(),class:b.className,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};}))")
print(btns_info)

# Click the SECOND Submit Rating button (the one at the bottom, text-white)
print("\nClicking second Submit Rating button...")
click_result = js("(function(){var btns=Array.from(document.querySelectorAll('button')).filter(function(b){return b.textContent.trim().includes('Submit Rating');});console.log('Found '+btns.length+' submit buttons');if(btns.length>=2){btns[1].click();return 'clicked button 2: '+btns[1].className;}else if(btns.length==1){btns[0].click();return 'clicked button 1: '+btns[0].className;}return 'no button found';})()")
print("Click result:", click_result)

# Poll for modal content for 10 seconds
print("\nWatching for modal content...")
for i in range(20):
    time.sleep(0.5)
    modal_info = js("(function(){var m=document.querySelector('.modal-container');if(!m)return 'no modal';return JSON.stringify({class:m.className,bodyText:m.querySelector('.body')?m.querySelector('.body').innerText:'',bodyHTML:m.querySelector('.body')?m.querySelector('.body').innerHTML.slice(0,200):'',allText:m.innerText.slice(0,200)});})()") 
    if modal_info and modal_info != 'no modal':
        d = json.loads(modal_info)
        if d.get('bodyText') or d.get('bodyHTML'):
            print(f"  t={i*0.5:.1f}s: {modal_info}")
            break
        else:
            print(f"  t={i*0.5:.1f}s: modal exists, body empty, class={d.get('class')}")
    else:
        print(f"  t={i*0.5:.1f}s: {modal_info}")

# Final URL check
print("\nFinal URL:", js('window.location.href'))
print("Final body:", js('document.body.innerText.slice(0,300)'))

ws.close()
