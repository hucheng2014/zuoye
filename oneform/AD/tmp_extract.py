import json, urllib.request
from websocket import create_connection
import time

CDP = 'http://browser:9223'

# Get page list
req = urllib.request.Request(f'{CDP}/json/list')
req.add_header('Host', 'localhost:9222')
resp = urllib.request.urlopen(req, timeout=5)
pages = json.loads(resp.read())
page = [p for p in pages if p['type'] == 'page'][0]
ws_url = page['webSocketDebuggerUrl'].replace('ws://localhost:9222', 'ws://browser:9223')

print(f"Connecting to: {ws_url[:80]}...")

ws = create_connection(ws_url, timeout=15, header=['Host: localhost:9222'])

def send_and_wait(payload):
    msg_id = payload['id']
    ws.send(json.dumps(payload))
    while True:
        raw = ws.recv()
        resp = json.loads(raw)
        if resp.get('id') == msg_id:
            return resp
        # Skip event notifications (no id field)

# Enable Runtime
send_and_wait({'id': 1, 'method': 'Runtime.enable', 'params': {}})
print("Runtime enabled")

# Extract page content - get inner text
resp = send_and_wait({'id': 2, 'method': 'Runtime.evaluate', 'params': {
    'expression': 'document.body ? document.body.innerText : "NO BODY"',
    'returnByValue': True
}})

val = resp.get('result', {}).get('result', {}).get('value', '')
print(f"\n=== PAGE TEXT ({len(val)} chars) ===")
print(val[:10000])

ws.close()
