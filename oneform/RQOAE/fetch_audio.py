"""通过浏览器 fetch API 下载音频（绕过 DNS/CDN 问题）"""
import json, urllib.request, sys, base64
from websocket import create_connection

CDP = 'http://browser:9223'
url = sys.argv[1] if len(sys.argv) > 1 else ''
output = sys.argv[2] if len(sys.argv) > 2 else '/tmp/audio.wav'

if 'api.tryrating.com/v1/catalog/catalog-items/' in url:
    url = url.replace(
        'https://api.tryrating.com/v1/catalog/catalog-items/',
        'https://www.tryrating.com/api/catalog/datasets/',
    )

req = urllib.request.Request(f'{CDP}/json/list')
req.add_header('Host', 'localhost:9222')
resp = urllib.request.urlopen(req, timeout=5)
pages = json.loads(resp.read())
ws_url = pages[0]['webSocketDebuggerUrl'].replace('ws://localhost:9222', 'ws://browser:9223')

ws = create_connection(ws_url, timeout=30, skip_utf8_validation=True)
ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
ws.settimeout(5)
try:
    while True:
        r = ws.recv()
        if '"id"' in r: break
except: pass

# Use browser's fetch to download and convert to base64
js = f"""(async () => {{
    try {{
        const resp = await fetch("{url}", {{ credentials: "include" }});
        if (!resp.ok) return 'ERROR:HTTP ' + resp.status;
        const blob = await resp.blob();
        if (blob.size < 1000) return 'ERROR:empty blob size=' + blob.size;
        const reader = new FileReader();
        return new Promise((resolve) => {{
            reader.onloadend = () => resolve(reader.result.split(',')[1]);
            reader.readAsDataURL(blob);
        }});
    }} catch(e) {{
        return 'ERROR:' + e.message;
    }}
}})()"""

ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': js, 'returnByValue': True, 'awaitPromise': True}}))
ws.settimeout(30)
try:
    while True:
        r = ws.recv()
        d = json.loads(r)
        if d.get('id') == 2:
            val = d.get('result', {}).get('result', {}).get('value', '')
            if val.startswith('ERROR:'):
                print(f'Download failed: {val}', file=sys.stderr)
                sys.exit(1)
            data = base64.b64decode(val)
            with open(output, 'wb') as f:
                f.write(data)
            print(f'Downloaded {len(data)} bytes to {output}')
            break
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
ws.close()
