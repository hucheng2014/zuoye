import json, urllib.request
from websocket import create_connection

CDP = 'http://browser:9223'

req = urllib.request.Request(f'{CDP}/json/list')
req.add_header('Host', 'localhost:9222')
resp = urllib.request.urlopen(req, timeout=5)
pages = json.loads(resp.read())
page = [p for p in pages if p['type'] == 'page'][0]
ws_url = page['webSocketDebuggerUrl'].replace('ws://localhost:9222', 'ws://browser:9223')

ws = create_connection(ws_url, timeout=15, header=['Host: localhost:9222'])

def send_and_wait(payload):
    msg_id = payload['id']
    ws.send(json.dumps(payload))
    while True:
        raw = ws.recv()
        resp = json.loads(raw)
        if resp.get('id') == msg_id:
            return resp

send_and_wait({'id': 1, 'method': 'Runtime.enable', 'params': {}})

# Get the HTML of all elements containing ad info
script = '''
(function() {
    var results = [];
    // Look for result-ad containers
    var adSections = document.querySelectorAll('[class*="result"], [class*="ad"], [class*="row"], [class*="task"], [class*="rating"]');
    for (var i = 0; i < adSections.length; i++) {
        var el = adSections[i];
        var text = el.innerText ? el.innerText.trim().substring(0, 500) : '';
        if (text.length > 10) {
            results.push({
                tag: el.tagName,
                classes: el.className,
                text: text
            });
        }
    }
    return JSON.stringify(results.slice(0, 20));
})();
'''
resp = send_and_wait({'id': 3, 'method': 'Runtime.evaluate', 'params': {
    'expression': script,
    'returnByValue': True
}})
val = resp.get('result', {}).get('result', {}).get('value', '')
results = json.loads(val)
for r in results:
    print(f"\n--- {r['tag']}.{r['classes']} ---")
    print(r['text'][:600])

ws.close()
