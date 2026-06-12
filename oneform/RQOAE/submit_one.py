#!/usr/bin/env python3
"""
Click a rating for one question and submit.
Usage: python3 submit_one.py <q_idx 0-2> <dot_idx 0-4> [--submit]
dot_idx: 0=Awful, 1=Poor, 2=Average, 3=Good, 4=Excellent
"""
import json, sys, time, urllib.request
from websocket import create_connection

CDP = 'http://browser:9223'
req = urllib.request.Request(f'{CDP}/json/list')
req.add_header('Host', 'localhost:9222')
pages = json.loads(urllib.request.urlopen(req, timeout=5).read())
ws_url = pages[0]['webSocketDebuggerUrl'].replace('ws://localhost:9222', 'ws://browser:9223')
ws = create_connection(ws_url, timeout=30, skip_utf8_validation=True)

msg_id = 0

def send(method, params=None):
    global msg_id
    msg_id += 1
    msg = {'id': msg_id, 'method': method}
    if params:
        msg['params'] = params
    ws.send(json.dumps(msg))
    ws.settimeout(15)
    while True:
        r = ws.recv()
        d = json.loads(r)
        if d.get('id') == msg_id:
            return d

def js(expr):
    r = send('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
    return r.get('result', {}).get('result', {}).get('value', '')

for domain in ['Runtime', 'DOM', 'Input']:
    send(f'{domain}.enable')

q_idx = int(sys.argv[1])   # 0, 1, or 2
dot_idx = int(sys.argv[2]) # 0=Awful 1=Poor 2=Average 3=Good 4=Excellent
do_submit = '--submit' in sys.argv

rating_names = ['Awful', 'Poor', 'Average', 'Good', 'Excellent']
print(f"Setting audio {q_idx} → {rating_names[dot_idx]} (dot {dot_idx})")

# Scroll into view
js(f'document.querySelectorAll(".rc-slider")[{q_idx}].scrollIntoView({{block:"center"}})')
time.sleep(0.8)

# Get slider coordinates
coord_js = f'''(function(){{
  var slider = document.querySelectorAll(".rc-slider")[{q_idx}];
  var rect = slider.getBoundingClientRect();
  var pcts = [0, 25, 50, 75, 100];
  return JSON.stringify({{
    x: rect.left + rect.width * pcts[{dot_idx}] / 100,
    y: rect.top + rect.height / 2,
    w: rect.width, h: rect.height, l: rect.left, t: rect.top
  }});
}})()'''

coords = json.loads(js(coord_js))
cx, cy = coords['x'], coords['y']
print(f"  Slider rect: left={coords['l']:.0f} top={coords['t']:.0f} w={coords['w']:.0f} h={coords['h']:.0f}")
print(f"  Clicking at ({cx:.1f}, {cy:.1f})")

send('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': cx, 'y': cy})
time.sleep(0.05)
send('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1})
time.sleep(0.05)
send('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1})
time.sleep(1.0)

# Verify
v = json.loads(js(f'''(function(){{
  var s = document.querySelectorAll(".rc-slider")[{q_idx}];
  var h = s.querySelector(".rc-slider-handle");
  var ad = s.querySelectorAll(".rc-slider-dot-active");
  return JSON.stringify({{handle: !!h, style: h ? h.getAttribute("style") : "", activeDots: ad.length}});
}})()'''))
print(f"  Verify: handle={v['handle']}, activeDots={v['activeDots']}, style={v['style']}")

if do_submit:
    print("\nSubmitting...")
    # Find and click Submit Rating button
    submit_js = '''(function(){
      var btns = Array.from(document.querySelectorAll("button"));
      var btn = btns.find(b => b.textContent.trim().includes("Submit Rating"));
      if(btn){ btn.click(); return "clicked: " + btn.textContent.trim(); }
      return "not found";
    })()'''
    result = js(submit_js)
    print(f"  Submit result: {result}")
    time.sleep(2)

ws.close()
print("Done!")
