"""Click rating dots - using correct audio indices (0, 1, 2)"""
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
    return result.get('result', {}).get('result', {}).get('value', '')

# Enable domains
for domain in ['Runtime', 'DOM', 'Input']:
    send_and_recv(f'{domain}.enable')

# First verify the audio sources to confirm mapping
for i in range(3):
    src = eval_js(f'document.querySelectorAll("audio")[{i}].src')
    print(f"Audio {i}: {src}")

print()

# Now there are only 3 audios and 3 sliders
# Audio 0 = outro_94_7 -> Poor (dot 1)
# Audio 1 = pre_42_7 -> Average (dot 2)  
# Audio 2 = post_32_2 -> Good (dot 3)
ratings = {0: 1, 1: 2, 2: 3}  # Poor, Average, Good
rating_names = {0: 'Awful', 1: 'Poor', 2: 'Average', 3: 'Good', 4: 'Excellent'}

for q_idx, dot_idx in ratings.items():
    print(f"\n=== Audio {q_idx}: selecting '{rating_names[dot_idx]}' ===")
    
    # Use the slider directly by index (there are 3 sliders matching 3 audios)
    # Scroll into view
    scroll_js = f'(function(){{var sliders=document.querySelectorAll(".rc-slider");sliders[{q_idx}].scrollIntoView({{block:"center"}});return "ok"}})()'
    eval_js(scroll_js)
    time.sleep(0.8)
    
    # Get coordinates
    coord_js = f'(function(){{var sliders=document.querySelectorAll(".rc-slider");var slider=sliders[{q_idx}];var rect=slider.getBoundingClientRect();var pcts=[0,25,50,75,100];var tx=rect.left+(rect.width*pcts[{dot_idx}]/100);var ty=rect.top+rect.height/2;return JSON.stringify({{x:tx,y:ty,l:rect.left,t:rect.top,w:rect.width,h:rect.height}})}})()'
    
    val = eval_js(coord_js)
    if not val:
        print(f"  ERROR: Could not get coordinates")
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
    time.sleep(1.0)
    
    # Verify
    verify_js = f'(function(){{var sliders=document.querySelectorAll(".rc-slider");var slider=sliders[{q_idx}];var handle=slider.querySelector(".rc-slider-handle");var activeDots=slider.querySelectorAll(".rc-slider-dot-active");var track=slider.querySelector(".rc-slider-track");return JSON.stringify({{handle:!!handle,handleStyle:handle?handle.getAttribute("style"):"none",active:activeDots.length,track:track?track.getAttribute("style"):"none"}})}})()'
    
    vval = eval_js(verify_js)
    if vval:
        vdata = json.loads(vval)
        print(f"  Result: handle={vdata['handle']}, activeDots={vdata['active']}")
        print(f"    handleStyle: {vdata['handleStyle']}")
        print(f"    trackStyle: {vdata['track']}")
        if not vdata['handle']:
            print("  WARNING: Click may not have registered! Trying alternative approach...")
            # Try clicking the dot directly
            dot_js = f'(function(){{var sliders=document.querySelectorAll(".rc-slider");var slider=sliders[{q_idx}];var dots=slider.querySelectorAll(".rc-slider-dot");var dot=dots[{dot_idx}];dot.click();return "clicked"}})()'
            eval_js(dot_js)
            time.sleep(0.5)
            # Re-verify
            vval2 = eval_js(verify_js)
            if vval2:
                vdata2 = json.loads(vval2)
                print(f"  After dot.click(): handle={vdata2['handle']}, activeDots={vdata2['active']}")
    
    time.sleep(0.5)

ws.close()
print("\nDone!")
