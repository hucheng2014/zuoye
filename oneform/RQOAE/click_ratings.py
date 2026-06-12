"""Click rating dots for all 3 questions using CDP mouse events"""
import json, urllib.request, time, sys
from websocket import create_connection

CDP = 'http://browser:9223'
req = urllib.request.Request(f'{CDP}/json/list')
req.add_header('Host', 'localhost:9222')
resp = urllib.request.urlopen(req, timeout=5)
pages = json.loads(resp.read())
ws_url = pages[0]['webSocketDebuggerUrl'].replace('ws://localhost:9222', 'ws://browser:9223')

ws = create_connection(ws_url, timeout=30, skip_utf8_validation=True)

# Enable required domains
for domain in ['Runtime', 'DOM', 'Input']:
    ws.send(json.dumps({'id': 100, 'method': f'{domain}.enable'}))
    ws.settimeout(5)
    try:
        while True:
            r = ws.recv()
            if '"id"' in r and '"100"' in r:
                break
    except:
        pass

# Ratings: question_index -> dot_index (0=Awful, 1=Poor, 2=Average, 3=Good, 4=Excellent)
ratings = {32: 1, 33: 2, 34: 3}  # Poor, Average, Good

msg_id = 1

def send_and_recv(method, params=None):
    global msg_id
    msg_id += 1
    msg = {'id': msg_id, 'method': method}
    if params:
        msg['params'] = params
    ws.send(json.dumps(msg))
    ws.settimeout(10)
    while True:
        r = ws.recv()
        d = json.loads(r)
        if d.get('id') == msg_id:
            return d
    return None

# For each question, get the slider position and click the appropriate dot
for q_idx, dot_idx in ratings.items():
    # Get the bounding rect of the slider for this question
    js = f'''(function(){{
var audios=document.querySelectorAll("audio");
var audio=audios[{q_idx}];
var el=audio;
while(el){{if(el.classList&&el.classList.contains("component-collection"))break;el=el.parentElement;}}
var ratingDiv=el.children[6];
var slider=ratingDiv.querySelector(".rc-slider");
var rect=slider.getBoundingClientRect();
var dot=slider.querySelectorAll(".rc-slider-dot")[{dot_idx}];
var dotRect=dot.getBoundingClientRect();
return JSON.stringify({{
  sliderX:rect.x,sliderY:rect.y,sliderW:rect.width,sliderH:rect.height,
  dotX:dotRect.x,dotY:dotRect.y,dotW:dotRect.width,dotH:dotRect.height
}});
}})()'''
    
    result = send_and_recv('Runtime.evaluate', {'expression': js, 'returnByValue': True})
    val = result.get('result', {}).get('result', {}).get('value', '')
    if not val:
        print(f"ERROR: Could not get slider rect for question {q_idx}")
        print(json.dumps(result, indent=2))
        continue
    
    coords = json.loads(val)
    # Click on the dot center
    click_x = coords['dotX'] + coords['dotW'] / 2
    click_y = coords['dotY'] + coords['dotH'] / 2
    
    # If dot is too small, click on the slider at the dot's x position
    if coords['dotW'] < 2:
        # Use slider rail position
        click_y = coords['sliderY'] + coords['sliderH'] / 2
    
    print(f"Question {q_idx}: clicking dot {dot_idx} at ({click_x:.1f}, {click_y:.1f})")
    
    # Simulate mouse click
    send_and_recv('Input.dispatchMouseEvent', {
        'type': 'mousePressed',
        'x': click_x,
        'y': click_y,
        'button': 'left',
        'clickCount': 1
    })
    time.sleep(0.1)
    send_and_recv('Input.dispatchMouseEvent', {
        'type': 'mouseReleased',
        'x': click_x,
        'y': click_y,
        'button': 'left',
        'clickCount': 1
    })
    time.sleep(0.5)
    
    # Verify the selection was made
    verify_js = f'''(function(){{
var audios=document.querySelectorAll("audio");
var audio=audios[{q_idx}];
var el=audio;
while(el){{if(el.classList&&el.classList.contains("component-collection"))break;el=el.parentElement;}}
var ratingDiv=el.children[6];
var slider=ratingDiv.querySelector(".rc-slider");
var handle=slider.querySelector(".rc-slider-handle");
var activeDots=slider.querySelectorAll(".rc-slider-dot-active");
return JSON.stringify({{
  handleExists:!!handle,
  handleStyle:handle?handle.getAttribute("style"):"none",
  activeDots:activeDots.length
}});
}})()'''
    
    verify = send_and_recv('Runtime.evaluate', {'expression': verify_js, 'returnByValue': True})
    vval = verify.get('result', {}).get('result', {}).get('value', '')
    if vval:
        vdata = json.loads(vval)
        print(f"  Verification: handle={vdata['handleExists']}, style={vdata['handleStyle']}, activeDots={vdata['activeDots']}")
    
    time.sleep(0.3)

ws.close()
print("\nDone clicking ratings!")
