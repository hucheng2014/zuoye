"""Click Submit Rating button"""
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
for domain in ['Runtime', 'Input']:
    send_and_recv(f'{domain}.enable')

# Find and click Submit Rating button
# First scroll to the bottom where the button is
eval_js('window.scrollTo(0, document.body.scrollHeight)')
time.sleep(0.5)

# Get Submit Rating button position
js = '''(function(){
var buttons = document.querySelectorAll("button");
for (var i = 0; i < buttons.length; i++) {
    if (buttons[i].textContent.trim() === "Submit Rating") {
        buttons[i].scrollIntoView({block: "center"});
        var rect = buttons[i].getBoundingClientRect();
        return JSON.stringify({x: rect.x + rect.width/2, y: rect.y + rect.height/2, w: rect.width, h: rect.height, text: buttons[i].textContent.trim(), disabled: buttons[i].disabled});
    }
}
return JSON.stringify({error: "Submit Rating button not found"});
})()'''

val = eval_js(js)
print(f"Submit button: {val}")

if val:
    data = json.loads(val)
    if 'error' not in data and not data.get('disabled'):
        click_x = data['x']
        click_y = data['y']
        print(f"Clicking Submit Rating at ({click_x:.1f}, {click_y:.1f})")
        
        time.sleep(0.5)
        send_and_recv('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': click_x, 'y': click_y})
        time.sleep(0.1)
        send_and_recv('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': click_x, 'y': click_y, 'button': 'left', 'clickCount': 1})
        time.sleep(0.05)
        send_and_recv('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': click_x, 'y': click_y, 'button': 'left', 'clickCount': 1})
        
        time.sleep(2)
        
        # Check if submission was successful (page might change or show confirmation)
        page_title = eval_js('document.title')
        page_url = eval_js('window.location.href')
        body_text = eval_js('document.body.textContent.substring(0, 500)')
        print(f"\nAfter submit:")
        print(f"  Title: {page_title}")
        print(f"  URL: {page_url}")
        print(f"  Body preview: {body_text[:200]}")
    else:
        print(f"Button issue: {data}")

ws.close()
