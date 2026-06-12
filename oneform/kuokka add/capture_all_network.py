import json
import urllib.request
import sys
import os
import time
import socket
from websocket import create_connection

def main():
    ports = [9233, 9232]
    pages = None
    for port in ports:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/json/list")
            with urllib.request.urlopen(req, timeout=5) as resp:
                pages = json.loads(resp.read())
                break
        except Exception: pass
    if not pages:
        print("Error connecting to CDP")
        sys.exit(1)
        
    page = [p for p in pages if p.get('type') == 'page' and "Annotation Tool" in p.get('title', '')][0]
    ws_url = page['webSocketDebuggerUrl']
    print(f"Connecting to page: {page['title']} ({ws_url})")
    
    ws = create_connection(ws_url, timeout=30)
    ws.settimeout(1.0) # Set timeout on WebSocket reads to 1 second
    
    # Enable Network domain
    ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
    try:
        ws.recv()
    except socket.timeout:
        pass
    
    # Reload page
    print("Reloading page to capture network headers...")
    ws.send(json.dumps({"id": 2, "method": "Page.reload"}))
    
    requests_log = []
    
    start_time = time.time()
    # Loop for 20 seconds to capture network events
    while time.time() - start_time < 20:
        try:
            raw = ws.recv()
            event = json.loads(raw)
            method = event.get("method")
            if method == "Network.requestWillBeSent":
                params = event.get("params", {})
                request = params.get("request", {})
                url = request.get("url", "")
                headers = request.get("headers", {})
                
                if "scilliance.com" in url:
                    requests_log.append({
                        "url": url,
                        "headers": headers
                    })
        except socket.timeout:
            # This is expected when no messages arrive
            continue
        except Exception as e:
            print("Error receiving:", e)
            break
            
    ws.close()
    
    persist_dir = "/Users/xaa/zuoye/oneform/kuokka add"
    output_path = os.path.join(persist_dir, "scilliance_requests.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(requests_log, f, indent=2, ensure_ascii=False)
        
    print(f"Saved {len(requests_log)} requests to {output_path}")
    
    # Specifically inspect requests to assets-public.scilliance.com
    assets_reqs = [r for r in requests_log if "assets-public.scilliance.com" in r['url']]
    print(f"\nFound {len(assets_reqs)} requests to assets-public.scilliance.com:")
    for idx, r in enumerate(assets_reqs):
        print(f"\nRequest {idx+1}: {r['url']}")
        print("Headers:")
        print(json.dumps(r['headers'], indent=2))

if __name__ == "__main__":
    main()
