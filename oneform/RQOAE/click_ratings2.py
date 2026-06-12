"""Click rating dots - scroll into view first, then use DOM click"""
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

def send_and_recv(method, params=None):
    global msg_id
    msg_id += 1
    msg = {'id': msg_id, 'method': method}
    if params:
        msg['params'] = params
    ws.send(json.dumps(msg))
    ws.settimeout(15)
    while True:
        r = ws.recv()
        d = json.loads(r)
        if d.get('id') == msg_id:
            return d

# Enable domains
for domain in ['Runtime', 'DOM', 'Input']:
    send_and_recv(f'{domain}.enable')

# Ratings: question_index -> dot_index (0=Awful, 1=Poor, 2=Average, 3=Good, 4=Excellent)
ratings = {32: 1, 33: 2, 34: 3}  # Poor, Average, Good
rating_names = {0: 'Awful', 1: 'Poor', 2: 'Average', 3: 'Good', 4: 'Excellent'}

for q_idx, dot_idx in ratings.items():
    print(f"\n=== Question {q_idx}: selecting '{rating_names[dot_idx]}' ===")
    
    # Scroll the slider into view and get viewport-relative coordinates
    js = f'''(function(){{
var audios=document.querySelectorAll("audio");
var audio=audios[{q_idx}];
var el=audio;
while(el){{if(el.classList&&el.classList.contains("component-collection"))break;el=el.parentElement;}}
var ratingDiv=el.children[6];
var slider=ratingDiv.querySelector(".rc-slider");
slider.scrollIntoView({{block:"center"}});
return "scrolled";
}})()'''
    
    send_and_recv('Runtime.evaluate', {'expression': js, 'returnByValue': True})
    time.sleep(0.5)
    
    # Now get the viewport-relative position after scrolling
    js2 = f'''(function(){{
var audios=document.querySelectorAll("audio");
var audio=audios[{q_idx}];
var el=audio;
while(el){{if(el.classList&&el.classList.contains("component-collection"))break;el=el.parentElement;}}
var ratingDiv=el.children[6];
var slider=ratingDiv.querySelector(".rc-slider");
var rect=slider.getBoundingClientRect();
var percentages=[0, 25, 50, 75, 100];
var targetX=rect.left + (rect.width * percentages[{dot_idx}] / 100);
var targetY=rect.top + rect.height/2;
return JSON.stringify({{x:targetX, y:targetY, sliderLeft:rect.left, sliderTop:rect.top, sliderW:rect.width, sliderH:rect.height}});
}})()'''
    
    result = send_and_recv('Runtime.evaluate', {'expression': js2, 'returnByValue': True})
    val = result.get('result', {}).get('result', {}).get('value', '')
    coords = json.loads(val)
    
    click_x = coords['x']
    click_y = coords['y']
    
    print(f"  Slider at ({coords['sliderLeft']:.0f}, {coords['sliderTop']:.0f}), size {coords['sliderW']:.0f}x{coords['sliderH']:.0f}")
    print(f"  Clicking at ({click_x:.1f}, {click_y:.1f})")
    
    # Mouse move first
    send_and_recv('Input.dispatchMouseEvent', {
        'type': 'mouseMoved',
        'x': click_x,
        'y': click_y
    })
    time.sleep(0.1)
    
    # Mouse down
    send_and_recv('Input.dispatchMouseEvent', {
        'type': 'mousePressed',
        'x': click_x,
        'y': click_y,
        'button': 'left',
        'clickCount': 1
    })
    time.sleep(0.05)
    
    # Mouse up
    send_and_recv('Input.dispatchMouseEvent', {
        'type': 'mouseReleased',
        'x': click_x,
        'y': click_y,
        'button': 'left',
        'clickCount': 1
    })
    time.sleep(0.5)
    
    # Verify
    verify_js = f'''(function(){{
var audios=document.querySelectorAll("audio");
var audio=audios[{q_idx}];
var el=audio;
while(el){{if(el.classList&&el.classList.contains("component-collection"))break;el=el.parentElement;}}
var ratingDiv=el.children[6];
var slider=ratingDiv.querySelector(".rc-slider");
var handle=slider.querySelector(".rc-slider-handle");
var activeDots=slider.querySelectorAll(".rc-slider-dot-active");
var track=slider.querySelector(".rc-slider-track");
return JSON.stringify({{
  handleExists:!!handle,
  handleStyle:handle?handle.getAttribute("style"):"none",
  activeDots:activeDots.length,
  trackStyle:track?track.getAttribute("style"):"none"
}});
}})()'''
    
    verify = send_and_recv('Runtime.evaluate', {'expression': verify_js, 'returnByValue': True})
    vval = verify.get('result', {}).get('result', {}).get('value', '')
    if vval:
        vdata = json.loads(vval)
        print(f"  Result: handle={vdata['handleExists']}, activeDots={vdata['activeDots']}, track={vdata['trackStyle']}")
    
    time.sleep(0.3)

ws.close()
print("\nDone!")
