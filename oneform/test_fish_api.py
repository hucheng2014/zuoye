import urllib.request
import json
import ssl

API_KEY = '70e3d7350cab4dcd93cd8a5cd25b9232'
REQ_URL = 'https://api.fish.audio/v1/models'

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(REQ_URL, headers={
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
})

try:
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read().decode())
        print('Models found:', len(data.get('items', [])))
        for item in data.get('items', [])[:10]:
            print(f"- ID: {item.get('_id')}, Title: {item.get('title')}, Lang: {item.get('language')}")
except Exception as e:
    print('Failed:', e)
    if hasattr(e, 'read'):
        print(e.read().decode())
