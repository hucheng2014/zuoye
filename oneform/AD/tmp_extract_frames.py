import json, urllib.request, html
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

script = '''
(function() {
    var results = [];
    var frames = document.querySelectorAll('iframe');
    for (var i = 0; i < frames.length; i++) {
        var srcdoc = frames[i].getAttribute('srcdoc') || '';
        // Decode HTML entities
        var decoded = srcdoc.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
        // Strip script tags
        decoded = decoded.replace(/<script[^>]*>[\\s\\S]*?<\\/script>/gi, '');
        // Strip style tags (keep content)
        // Get text content
        var div = document.createElement('div');
        div.innerHTML = decoded;
        var text = div.textContent || div.innerText || '';
        text = text.replace(/\\s+/g, ' ').trim();
        results.push({
            index: i,
            text: text.substring(0, 2000),
            srcdoc: decoded.substring(0, 3000)
        });
    }
    return JSON.stringify(results);
})();
'''

resp = send_and_wait({'id': 2, 'method': 'Runtime.evaluate', 'params': {
    'expression': script,
    'returnByValue': True
}})
val = resp.get('result', {}).get('result', {}).get('value', '')
frames = json.loads(val)

print(f"Total iframes: {len(frames)}")

# Now need to figure out which task each iframe belongs to.
# Let's also get the task container structure
script2 = '''
(function() {
    var tasks = [];
    var rows = document.querySelectorAll('.row.ml-0.mr-0, [class*="task-container"] > div');
    // Better: look for the request ID containers
    var containers = document.querySelectorAll('[class*="row-default"], .tr-row-container');
    
    // Look for iframes grouped by task - the iframes are inside DIVs with class "html-component"
    var htmlComponents = document.querySelectorAll('.html-component iframe');
    for (var i = 0; i < htmlComponents.length; i++) {
        var srcdoc = htmlComponents[i].getAttribute('srcdoc') || '';
        var decoded = srcdoc.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
        decoded = decoded.replace(/<script[^>]*>[\\s\\S]*?<\\/script>/gi, '');
        var div = document.createElement('div');
        div.innerHTML = decoded;
        var text = div.textContent || div.innerText || '';
        text = text.replace(/\\s+/g, ' ').trim().substring(0, 1500);
    }
    
    // Group iframes by the TaskAPI id
    var iframes = document.querySelectorAll('iframe');
    var groups = {};
    for (var i = 0; i < iframes.length; i++) {
        var srcdoc = iframes[i].getAttribute('srcdoc') || '';
        var match = srcdoc.match(/TaskAPI_Html_([a-zA-Z0-9_-]+)/);
        if (match) {
            var tplName = match[1];
            // Get the unique task identifier from the full TaskAPI name
            var fullMatch = srcdoc.match(/TaskAPI_Html_[^_]+_(01KT1D2[^"&]+)/);
            if (fullMatch) {
                var taskId = fullMatch[1];
                if (!groups[taskId]) groups[taskId] = [];
                groups[taskId].push({idx: i, tpl: tplName});
            }
        }
    }
    return JSON.stringify(groups);
})();
'''

resp = send_and_wait({'id': 3, 'method': 'Runtime.evaluate', 'params': {
    'expression': script2,
    'returnByValue': True
}})
val = resp.get('result', {}).get('result', {}).get('value', '')
groups = json.loads(val)
print(f"\nIframe groups by task: {len(groups)}")
for tid, members in groups.items():
    print(f"  Task {tid}: {len(members)} iframes, templates: {[m['tpl'] for m in members]}, indices: {[m['idx'] for m in members]}")

ws.close()
