"""Click radio buttons for Broad Match ratings"""
import json, urllib.request, time
from websocket import create_connection

CDP = 'http://browser:9223'
req = urllib.request.Request(f'{CDP}/json/list')
req.add_header('Host', 'localhost:9222')
resp = urllib.request.urlopen(req, timeout=5)
pages = json.loads(resp.read())
ws_url = pages[0]['webSocketDebuggerUrl'].replace('ws://localhost:9222', 'ws://browser:9223')

ws = create_connection(ws_url, timeout=30, skip_utf8_validation=True)

msg_id = 0

def eval_js(js):
    global msg_id
    msg_id += 1
    ws.send(json.dumps({'id': msg_id, 'method': 'Runtime.evaluate', 'params': {'expression': js, 'returnByValue': True}}))
    ws.settimeout(10)
    while True:
        r = ws.recv()
        d = json.loads(r)
        if d.get('id') == msg_id:
            return d.get('result', {}).get('result', {}).get('value', '')

# Ratings for each question (radio button index to click)
# Q1: Good(0), Q2: Good(3), Q3: Acceptable(7), Q4: Acceptable(10),
# Q5: Bad(14), Q6: Good(15), Q7: Acceptable(19), Q8: Acceptable(22),
# Q9: Good(24), Q10: Good(27)
clicks = [0, 3, 7, 10, 14, 15, 19, 22, 24, 27]

# Click each radio button
js = '''(function(){
var inputs = document.querySelectorAll('input[type="radio"]');
var clicks = ''' + json.dumps(clicks) + ''';
var results = [];
for(var i=0; i<clicks.length; i++){
  var idx = clicks[i];
  var inp = inputs[idx];
  if(inp){
    inp.click();
    results.push({idx: idx, name: inp.name, value: inp.value, checked: inp.checked});
  } else {
    results.push({idx: idx, error: 'not found'});
  }
}
return JSON.stringify(results);
})()'''

result = eval_js(js)
if result:
    data = json.loads(result)
    for item in data:
        print(json.dumps(item))
else:
    print("ERROR: no result")

# Verify all selections
time.sleep(0.5)
verify_js = '''(function(){
var inputs = document.querySelectorAll('input[type="radio"]');
var checked = [];
for(var i=0;i<inputs.length;i++){
  if(inputs[i].checked) checked.push({index:i, name:inputs[i].name, value:inputs[i].value});
}
return JSON.stringify(checked);
})()'''

vresult = eval_js(verify_js)
if vresult:
    vdata = json.loads(vresult)
    print(f"\nVerification - {len(vdata)} selections made:")
    for item in vdata:
        print(f"  Q{item['index']//3 + 1}: {item['value']}")

ws.close()
print("\nDone!")
