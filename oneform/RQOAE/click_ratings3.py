"""Click rating dots - robust version with error handling"""
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

def eval_js(js):
    result = send_and_recv('Runtime.evaluate', {'expression': js, 'returnByValue': True})
    val = result.get('result', {}).get('result', {}).get('value', '')
    return val

# Enable domains
for domain in ['Runtime', 'DOM', 'Input']:
    send_and_recv(f'{domain}.enable')

# Ratings: question_index -> dot_index (0=Awful, 1=Poor, 2=Average, 3=Good, 4=Excellent)
ratings = {32: 1, 33: 2, 34: 3}  # Poor, Average, Good
rating_names = {0: 'Awful', 1: 'Poor', 2: 'Average', 3: 'Good', 4: 'Excellent'}

for q_idx, dot_idx in ratings.items():
    print(f"\n=== Question {q_idx}: selecting '{rating_names[dot_idx]}' ===")
    
    # Scroll the slider into view
    scroll_js = f'(function(){{var audios=document.querySelectorAll("audio");var audio=audios[{q_idx}];var el=audio;while(el){{if(el.classList&&el.classList.contains("component-collection"))break;el=el.parentElement;}}var ratingDiv=el.children[6];var slider=ratingDiv.querySelector(".rc-slider");slider.scrollIntoView({{block:"center"}});return "ok"}})()'
    eval_js(scroll_js)
    time.sleep(0.8)
    
    # Get coordinates
    coord_js = f'(function(){{var audios=document.querySelectorAll("audio");var audio=audios[{q_idx}];var el=audio;while(el){{if(el.classList&&el.classList.contains("component-collection"))break;el=el.parentElement;}}var ratingDiv=el.children[6];var slider=ratingDiv.querySelector(".rc-slider");var rect=slider.getBoundingClientRect();var pcts=[0,25,50,75,100];var tx=rect.left+(rect.width*pcts[{dot_idx}]/100);var ty=rect.top+rect.height/2;return JSON.stringify({{x:tx,y:ty,l:rect.left,t:rect.top,w:rect.width,h:rect.height}})}})()'
    
    val = eval_js(coord_js)
    if not val:
        print(f"  ERROR: Could not get coordinates, retrying...")
        time.sleep(1)
        val = eval_js(coord_js)
    
    if not val:
        print(f"  ERROR: Still no coordinates, skipping")
        continue
    
    coords = json.loads(val)
    click_x = coords['x']
    click_y = coords['y']
    
    print(f"  Slider at ({coords['l']:.0f}, {coords['t']:.0f}), size {coords['w']:.0f}x{coords['h']:.0f}")
    print(f"  Clicking at ({click_x:.1f}, {click_y:.1f})")
    
    # Perform click
    send_and_recv('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': click_x, 'y': click_y})
    time.sleep(0.05)
    send_and_recv('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': click_x, 'y': click_y, 'button': 'left', 'clickCount': 1})
    time.sleep(0.05)
    send_and_recv('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': click_x, 'y': click_y, 'button': 'left', 'clickCount': 1})
    time.sleep(0.8)
    
    # Verify
    verify_js = f'(function(){{var audios=document.querySelectorAll("audio");var audio=audios[{q_idx}];var el=audio;while(el){{if(el.classList&&el.classList.contains("component-collection"))break;el=el.parentElement;}}var ratingDiv=el.children[6];var slider=ratingDiv.querySelector(".rc-slider");var handle=slider.querySelector(".rc-slider-handle");var activeDots=slider.querySelectorAll(".rc-slider-dot-active");var track=slider.querySelector(".rc-slider-track");return JSON.stringify({{handle:!!handle,handleStyle:handle?handle.getAttribute("style"):"none",active:activeDots.length,track:track?track.getAttribute("style"):"none"}})}})()'
    
    vval = eval_js(verify_js)
    if vval:
        vdata = json.loads(vval)
        print(f"  Result: handle={vdata['handle']}, activeDots={vdata['active']}")
        print(f"    handleStyle: {vdata['handleStyle']}")
        print(f"    trackStyle: {vdata['track']}")
        if not vdata['handle']:
            print("  WARNING: Click may not have registered!")
    
    time.sleep(0.5)

ws.close()
print("\nDone!")
