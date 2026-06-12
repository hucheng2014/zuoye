"""Debug why JS evaluation returns empty"""
import json, urllib.request, time
from websocket import create_connection

CDP = 'http://browser:9223'
req = urllib.request.Request(f'{CDP}/json/list')
req.add_header('Host', 'localhost:9222')
resp = urllib.request.urlopen(req, timeout=5)
pages = json.loads(resp.read())
ws_url = pages[0]['webSocketDebuggerUrl'].replace('ws://localhost:9222', 'ws://browser:9223')

ws = create_connection(ws_url, timeout=30, skip_utf8_validation=True)

msg_id = 0

def send_and_recv(method, params=None):
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

# Enable Runtime
send_and_recv('Runtime.enable')

# Simple test
result = send_and_recv('Runtime.evaluate', {'expression': '1+1', 'returnByValue': True})
print(f"Simple test: {result.get('result', {}).get('result', {})}")

# Test audio count
result = send_and_recv('Runtime.evaluate', {'expression': 'document.querySelectorAll("audio").length', 'returnByValue': True})
print(f"Audio count: {result.get('result', {}).get('result', {})}")

# Test finding slider for q32
js = 'document.querySelectorAll(".rc-slider").length'
result = send_and_recv('Runtime.evaluate', {'expression': js, 'returnByValue': True})
print(f"Slider count: {result.get('result', {}).get('result', {})}")

# Get all sliders
js = '(function(){var sliders=document.querySelectorAll(".rc-slider");var r=[];for(var i=0;i<sliders.length;i++){r.push(i);}return JSON.stringify(r)})()'
result = send_and_recv('Runtime.evaluate', {'expression': js, 'returnByValue': True})
print(f"Sliders: {result.get('result', {}).get('result', {}).get('value', '')}")

# Try to get the slider for q32 step by step
js = '(function(){var audios=document.querySelectorAll("audio");return audios.length})()'
result = send_and_recv('Runtime.evaluate', {'expression': js, 'returnByValue': True})
print(f"Audios via IIFE: {result.get('result', {}).get('result', {})}")

# Check if component-collection exists
js = 'document.querySelectorAll(".component-collection").length'
result = send_and_recv('Runtime.evaluate', {'expression': js, 'returnByValue': True})
print(f"Component collections: {result.get('result', {}).get('result', {})}")

# Try the full query but return intermediate results
js = '''(function(){
var audios = document.querySelectorAll("audio");
if (audios.length < 33) return "not enough audios: " + audios.length;
var audio = audios[32];
if (!audio) return "audio 32 is null";
var el = audio;
var levels = 0;
while (el) {
    if (el.classList && el.classList.contains("component-collection")) break;
    el = el.parentElement;
    levels++;
}
if (!el) return "no component-collection found after " + levels + " levels";
if (!el.children[6]) return "no child 6, children count: " + el.children.length;
var ratingDiv = el.children[6];
var slider = ratingDiv.querySelector(".rc-slider");
if (!slider) return "no slider in ratingDiv, html: " + ratingDiv.innerHTML.substring(0, 200);
var rect = slider.getBoundingClientRect();
return JSON.stringify({x: rect.x, y: rect.y, w: rect.width, h: rect.height});
})()'''

result = send_and_recv('Runtime.evaluate', {'expression': js, 'returnByValue': True})
val = result.get('result', {}).get('result', {}).get('value', '')
print(f"\nFull query result: {val}")
if not val:
    print(f"Full response: {json.dumps(result, indent=2)}")

ws.close()
