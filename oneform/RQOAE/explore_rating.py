"""Explore rating control structure"""
import json, urllib.request
from websocket import create_connection

CDP = 'http://browser:9223'
req = urllib.request.Request(f'{CDP}/json/list')
req.add_header('Host', 'localhost:9222')
resp = urllib.request.urlopen(req, timeout=5)
pages = json.loads(resp.read())
ws_url = pages[0]['webSocketDebuggerUrl'].replace('ws://localhost:9222', 'ws://browser:9223')

ws = create_connection(ws_url, timeout=15, skip_utf8_validation=True)

# Get the rating control structure for all 3 questions
js = '''(function(){
var audios=document.querySelectorAll("audio");
var results=[];
for(var q=32;q<=34;q++){
  var audio=audios[q];
  var el=audio;
  while(el){if(el.classList&&el.classList.contains("component-collection"))break;el=el.parentElement;}
  if(!el)continue;
  var ratingDiv=el.children[6];
  var items=ratingDiv.querySelectorAll("*");
  var clickables=[];
  for(var i=0;i<items.length;i++){
    var item=items[i];
    var t=item.textContent.trim();
    if(t==="Awful"||t==="Poor"||t==="Average"||t==="Good"||t==="Excellent"){
      if(item.children.length===0||item.children.length===1){
        clickables.push({tag:item.tagName,cls:(item.className||"").substring(0,100),text:t,parent:item.parentElement.tagName+"."+item.parentElement.className.substring(0,50)});
      }
    }
  }
  results.push({q:q,clickables:clickables});
}
return JSON.stringify(results);
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
            for item in data:
                print(f"\n=== Question {item['q']} ===")
                for c in item['clickables']:
                    print(f"  {c['tag']}.{c['cls']}: '{c['text']}' (parent: {c['parent']})")
        else:
            print(json.dumps(d.get('result', {}), indent=2))
        break
ws.close()
