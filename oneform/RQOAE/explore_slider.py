"""Explore rc-slider structure to understand how to set values"""
import json, urllib.request
from websocket import create_connection

CDP = 'http://browser:9223'
req = urllib.request.Request(f'{CDP}/json/list')
req.add_header('Host', 'localhost:9222')
resp = urllib.request.urlopen(req, timeout=5)
pages = json.loads(resp.read())
ws_url = pages[0]['webSocketDebuggerUrl'].replace('ws://localhost:9222', 'ws://browser:9223')

ws = create_connection(ws_url, timeout=15, skip_utf8_validation=True)

# Get slider structure details
js = '''(function(){
var audios=document.querySelectorAll("audio");
var audio=audios[32];
var el=audio;
while(el){if(el.classList&&el.classList.contains("component-collection"))break;el=el.parentElement;}
var ratingDiv=el.children[6];
var slider=ratingDiv.querySelector(".rc-slider");
if(!slider)return JSON.stringify({error:"no slider found"});

var handle=slider.querySelector(".rc-slider-handle");
var marks=slider.querySelectorAll(".rc-slider-mark-text");
var dots=slider.querySelectorAll(".rc-slider-dot");
var step=slider.querySelector(".rc-slider-step");
var rail=slider.querySelector(".rc-slider-rail");
var track=slider.querySelector(".rc-slider-track");

var markInfo=[];
for(var i=0;i<marks.length;i++){
  markInfo.push({text:marks[i].textContent,style:marks[i].getAttribute("style")});
}

var dotInfo=[];
for(var i=0;i<dots.length;i++){
  dotInfo.push({style:dots[i].getAttribute("style"),cls:dots[i].className});
}

return JSON.stringify({
  sliderClass:slider.className,
  handleStyle:handle?handle.getAttribute("style"):"none",
  handleAriaValue:handle?handle.getAttribute("aria-valuenow"):"none",
  handleAriaMin:handle?handle.getAttribute("aria-valuemin"):"none",
  handleAriaMax:handle?handle.getAttribute("aria-valuemax"):"none",
  marks:markInfo,
  dots:dotInfo,
  railRect:rail?{w:rail.offsetWidth,h:rail.offsetHeight}:null,
  sliderRect:{w:slider.offsetWidth,h:slider.offsetHeight}
});
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
            print(json.dumps(data, indent=2))
        else:
            print(json.dumps(d.get('result', {}), indent=2))
        break
ws.close()
