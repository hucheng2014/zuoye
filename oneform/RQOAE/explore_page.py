"""Explore page structure to find rating controls"""
import json, urllib.request
from websocket import create_connection

CDP = 'http://browser:9223'
req = urllib.request.Request(f'{CDP}/json/list')
req.add_header('Host', 'localhost:9222')
resp = urllib.request.urlopen(req, timeout=5)
pages = json.loads(resp.read())
ws_url = pages[0]['webSocketDebuggerUrl'].replace('ws://localhost:9222', 'ws://browser:9223')

ws = create_connection(ws_url, timeout=15, skip_utf8_validation=True)

js = '(function(){var audios=document.querySelectorAll("audio");var audio=audios[32];var el=audio;while(el){if(el.classList&&el.classList.contains("component-collection"))break;el=el.parentElement;}if(!el)return JSON.stringify({error:"NOT FOUND"});var children=[];for(var i=0;i<el.children.length;i++){var child=el.children[i];children.push({i:i,tag:child.tagName,cls:(child.className||"").substring(0,80),text:child.textContent.trim().substring(0,100),cc:child.children.length});}return JSON.stringify(children);})()'

ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': js, 'returnByValue': True}}))
ws.settimeout(10)
while True:
    r = ws.recv()
    d = json.loads(r)
    if d.get('id') == 1:
        val = d.get('result', {}).get('result', {}).get('value', '')
        if val:
            data = json.loads(val)
            for item in data:
                print(json.dumps(item))
        else:
            print(json.dumps(d.get('result', {}), indent=2))
        break
ws.close()
