import json, urllib.request, re
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

# Extract all iframe srcdoc contents, decoded
script = '''
(function() {
    var allData = {};
    // First find query text outside iframes - the task containers with query and locale
    var queryText = '';
    var localeText = '';
    var taskRows = document.querySelectorAll('[class*="tr-row"]');
    
    // Get page title to understand context
    var pageText = document.body.innerText || '';
    
    // Extract all iframes with their full srcdoc
    var iframes = document.querySelectorAll('iframe');
    for (var i = 0; i < iframes.length; i++) {
        var srcdoc = iframes[i].getAttribute('srcdoc') || '';
        // Decode HTML entities
        var decoded = srcdoc
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&')
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'");
            
        // Get task ID from srcdoc
        var taskMatch = srcdoc.match(/TaskAPI_Html_[^_]+_(01KT1D2[^"&]+)/);
        var taskId = taskMatch ? taskMatch[1] : 'unknown_' + i;
        
        // Get template name
        var tplMatch = srcdoc.match(/TaskAPI_Html_([a-zA-Z0-9_-]+)_01KT1D2/);
        var tplName = tplMatch ? tplMatch[1] : 'unknown';
        
        // Strip script tags
        decoded = decoded.replace(/<script[^>]*>[\\s\\S]*?<\\/script>/gi, '');
        // Strip style tags
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
    
    // Also get query text from page
    var queryEls = document.querySelectorAll('[class*="query"], [class*="Query"], td, th, .sd-richtext');
    var queries = [];
    var seen = {};
    for (var i = 0; i < queryEls.length; i++) {
        var el = queryEls[i];
        var text = (el.textContent || '').trim();
        if (text && text.length > 3 && text.length < 200 && !seen[text]) {
            seen[text] = true;
            queries.push(text);
        }
    }
    allData['__page_queries__'] = queries;
    
    return JSON.stringify(allData);
})();
'''

resp = send_and_wait({'id': 2, 'method': 'Runtime.evaluate', 'params': {
    'expression': script,
    'returnByValue': True
}})
val = resp.get('result', {}).get('result', {}).get('value', '')
allData = json.loads(val)

# Get page queries
queries = allData.pop('__page_queries__', [])
print("=== PAGE QUERIES ===")
for q in queries:
    print(f"  {q}")

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
        print(f"Text: {data['text'][:2000]}")
        print(f"\n--- HTML ---")
        print(data['fullHtml'][:3000])

ws.close()
