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

# Try to get iframes and also get the outerHTML of each task row
script = '''
(function() {
    var results = {};
    
    // Check for iframes
    results.iframes = [];
    var frames = document.querySelectorAll('iframe');
    for (var i = 0; i < frames.length; i++) {
        results.iframes.push({
            src: frames[i].src,
            outerHTML: frames[i].outerHTML.substring(0, 300)
        });
    }
    
    // Get all "RESULT AD" parent elements' inner HTML
    results.adHTMLs = [];
    var allDivs = document.querySelectorAll('div');
    for (var i = 0; i < allDivs.length; i++) {
        var innerText = allDivs[i].innerText || '';
        if (innerText.indexOf('RESULT AD') >= 0 && innerText.indexOf('QUERY') < 0) {
            results.adHTMLs.push({
                className: allDivs[i].className,
                innerHTML: allDivs[i].innerHTML.substring(0, 1000),
                innerText: allDivs[i].innerText.substring(0, 500)
            });
        }
    }
    
    // Try to find any img elements near the ads
    results.images = [];
    var imgs = document.querySelectorAll('img');
    for (var i = 0; i < imgs.length; i++) {
        results.images.push({
            src: imgs[i].src,
            alt: imgs[i].alt,
            className: imgs[i].className,
            width: imgs[i].width,
            height: imgs[i].height
        });
    }
    
    return JSON.stringify(results);
})();
'''
resp = send_and_wait({'id': 3, 'method': 'Runtime.evaluate', 'params': {
    'expression': script,
    'returnByValue': True
}})
val = resp.get('result', {}).get('result', {}).get('value', '')
results = json.loads(val)
print("=== IFRAMES ===")
for f in results.get('iframes', []):
    print(f"src={f['src']}")
    print(f"outerHTML={f['outerHTML']}")
print("\n=== AD HTMLS (around RESULT AD) ===")
for h in results.get('adHTMLs', []):
    print(f"\nClass: {h['className']}")
    print(f"innerText: {h['innerText']}")
    print(f"innerHTML: {h['innerHTML']}")
print("\n=== IMAGES ===")
for img in results.get('images', []):
    print(f"src={img['src']}, alt={img['alt']}, class={img['className']}")

ws.close()
