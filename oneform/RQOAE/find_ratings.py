"""Find rating controls on the Broad Match page"""
import json, urllib.request
from websocket import create_connection

CDP = 'http://browser:9223'
req = urllib.request.Request(f'{CDP}/json/list')
req.add_header('Host', 'localhost:9222')
resp = urllib.request.urlopen(req, timeout=5)
pages = json.loads(resp.read())
ws_url = pages[0]['webSocketDebuggerUrl'].replace('ws://localhost:9222', 'ws://browser:9223')

ws = create_connection(ws_url, timeout=30, skip_utf8_validation=True)

js = '''(function(){
var inputs = document.querySelectorAll('input[type="radio"]');
var results = [];
for(var i=0;i<inputs.length;i++){
  var inp = inputs[i];
  var label = inp.parentElement ? inp.parentElement.textContent.trim() : '';
  if(!label){
    var lbl = document.querySelector('label[for="'+inp.id+'"]');
    if(lbl) label = lbl.textContent.trim();
  }
  results.push({index: i, name: inp.name, value: inp.value, id: inp.id, label: label.substring(0,30), checked: inp.checked});
}
return JSON.stringify({total: inputs.length, items: results.slice(0, 40)});
})()'''

ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': js, 'returnByValue': True}}))
ws.settimeout(10)
while True:
    r = ws.recv()
    d = json.loads(r)
    if d.get('id') == 1:
        val = d.get('result', {}).get('result', {}).get('value', '')
        if val:
            data = json.loads(val)
            print(f"Total radio inputs: {data['total']}")
            for item in data['items']:
                print(json.dumps(item))
        else:
            print("No value returned")
            print(json.dumps(d.get('result', {})))
        break
ws.close()
