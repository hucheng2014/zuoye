import json, urllib.request, re
from websocket import create_connection

# CDP on host (browser in Docker exposed on 9233)
CDP = 'http://127.0.0.1:9233'

req = urllib.request.Request(f'{CDP}/json/list')
resp = urllib.request.urlopen(req, timeout=10)
pages = json.loads(resp.read())
print(f"Found {len(pages)} pages/workers")

page = [p for p in pages if p['type'] == 'page'][0]
ws_url = page['webSocketDebuggerUrl']
print(f"WS URL: {ws_url}")

ws = create_connection(ws_url, timeout=15)

def send_and_wait(payload):
    msg_id = payload['id']
    ws.send(json.dumps(payload))
    while True:
        raw = ws.recv()
        resp = json.loads(raw)
        if resp.get('id') == msg_id:
            return resp
        # Check for errors
        if 'error' in resp:
            print(f"ERROR response: {json.dumps(resp)[:200]}")

send_and_wait({'id': 1, 'method': 'Runtime.enable', 'params': {}})

script = '''
(function() {
    var results = [];
    
    // Try to find task rows (TryRating classic layout)
    var taskContainers = document.querySelectorAll('[class*="task"], [class*="Task"], .task-item, .rating-item, [data-task-id]');
    
    // Get all iframe srcdoc contents
    var iframes = document.querySelectorAll('iframe');
    var allData = {};
    
    for (var i = 0; i < iframes.length; i++) {
        var srcdoc = iframes[i].getAttribute('srcdoc') || '';
        var decoded = srcdoc
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&')
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'");
        
        // Get task ID
        var taskMatch = srcdoc.match(/TaskAPI_Html_[^_]+_(01KT1D2[^"&]+)/);
        var taskId = taskMatch ? taskMatch[1] : 'unknown_' + i;
        
        // Get template name
        var tplMatch = srcdoc.match(/TaskAPI_Html_([a-zA-Z0-9_-]+)_01KT1D2/);
        var tplName = tplMatch ? tplMatch[1] : 'unknown';
        
        // Strip script and style tags
        decoded = decoded.replace(/<script[^>]*>[\\s\\S]*?<\\/script>/gi, '');
        decoded = decoded.replace(/<style[^>]*>[\\s\\S]*?<\\/style>/gi, '');
        
        var div = document.createElement('div');
        div.innerHTML = decoded;
        var text = (div.textContent || div.innerText || '').replace(/\\s+/g, ' ').trim();
        
        var baseTaskId = taskId.replace(/_[a-zA-Z0-9]+$/, '');
        var key = baseTaskId + '___' + tplName;
        allData[key] = {
            text: text.substring(0, 3000),
            fullHtml: decoded.substring(0, 5000)
        };
    }
    
    // Get query texts from the page body
    var allText = document.body.innerText || '';
    allData['__full_page_text__'] = allText.substring(0, 5000);
    allData['__page_title__'] = document.title || '';
    
    // Get query/locale from page text
    var lines = allText.split('\\n').filter(function(l) { return l.trim().length > 0 && l.trim().length < 300; });
    allData['__page_lines__'] = lines.slice(0, 100);
    
    return JSON.stringify(allData);
})();
'''

resp = send_and_wait({'id': 2, 'method': 'Runtime.evaluate', 'params': {
    'expression': script,
    'returnByValue': True
}})
val = resp.get('result', {}).get('result', {}).get('value', '')
allData = json.loads(val)

# Extract page info
full_page = allData.pop('__full_page_text__', '')
page_title = allData.pop('__page_title__', '')
page_lines = allData.pop('__page_lines__', [])

print(f"=== PAGE TITLE: {page_title} ===")
print(f"\n=== PAGE LINES ===")
for line in page_lines:
    print(f"  [{line}]")

# Group by task
tasks = {}
for key, data in allData.items():
    parts = key.split('___')
    if len(parts) == 2:
        taskId, tpl = parts
        if taskId not in tasks:
            tasks[taskId] = {}
        tasks[taskId][tpl] = data

print(f"\n=== TOTAL TASKS: {len(tasks)} ===")
for i, (taskId, tpls) in enumerate(sorted(tasks.items())):
    print(f"\n{'='*60}")
    print(f"TASK {i+1}: {taskId}")
    print(f"{'='*60}")
    for tplName in sorted(tpls.keys()):
        data = tpls[tplName]
        print(f"\n--- Template: {tplName} ---")
        print(f"Text: {data['text']}")

ws.close()
