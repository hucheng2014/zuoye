import json, urllib.request, time, re, sys

CDP = 'http://browser:9223'

def _h(h):
    return {'Host': 'localhost:9222', 'Content-Type': 'application/json'}

def cdp(url, method='GET', body=None):
    start = f'{CDP}/json'
    idx = [p['id'] for p in json.loads(urllib.request.urlopen(
        urllib.request.Request(f'{start}/list', headers=_h({})))).read()) if 'page' in p['type']]
    ws_url = [p['webSocketDebuggerUrl'] for p in json.loads(urllib.request.urlopen(
        urllib.request.Request(f'{start}/list', headers=_h({})))).read()) if 'page' in p['type']][0]
    
    # Use HTTP-based CDP
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(f'{CDP}/json/{method}/{idx[0]}', data=data, headers=_h({'Content-Type': 'application/json'}), method='POST')
    if body:
        req = urllib.request.Request(f'{CDP}/json/{method}/{idx[0]}' if method != 'Runtime.evaluate' else f'{CDP}/json/Runtime.evaluate/{idx[0]}', 
                                    data=json.dumps(body).encode(), headers=_h({'Content-Type': 'application/json'}), method='POST')
    
    # Actually let me use a simpler approach - the /json/protocol endpoint
    pass

# Simpler approach: direct HTTP to CDP
def send_cdp(method, params=None):
    idx = [p['id'] for p in json.loads(urllib.request.urlopen(
        urllib.request.Request(f'{CDP}/json/list', headers=_h({})))).read()) if 'page' in p['type']]
    if not idx:
        raise Exception('No page found')
    
    # Use the new CDP endpoint 
    data = {'method': method, 'params': params or {}}
    req_url = f'{CDP}/json/execute/{idx[0]}'
    data_bytes = json.dumps(data).encode()
    req = urllib.request.Request(req_url, data=data_bytes, headers=_h({'Content-Type': 'application/json'}), method='POST')
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())
    except Exception as e:
        print(f'CDP error for {method}: {e}', file=sys.stderr)
        return None

# Extract page content
html = send_cdp('Runtime.evaluate', {'expression': 'document.body.innerText', 'returnByValue': True})
if html and 'result' in html:
    result = html.get('result', {})
    if 'result' in result:
        text = result['result'].get('value', '')
    elif 'value' in result:
        text = result['value']
    else:
        text = json.dumps(html)
else:
    text = str(html)

print("=== PAGE TEXT ===")
print(text[:8000])
print("\n=== END ===")
