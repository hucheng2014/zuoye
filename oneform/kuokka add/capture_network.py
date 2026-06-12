import json
import urllib.request
import sys
import os
import time
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
    
    # Enable Network domain
    ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
    ws.recv()
    
    # Reload page
    print("Reloading page to capture network headers...")
    ws.send(json.dumps({"id": 2, "method": "Page.reload"}))
    
    token = None
    headers_dict = {}
    
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
                
                # Check for Authorization header
                auth_header = None
                for h in headers:
                    if h.lower() == "authorization":
                        auth_header = headers[h]
                        break
                        
                if auth_header:
                    print(f"Found Authorization header in request to: {url}")
                    token = auth_header
                    headers_dict = headers
                    # Save token to file
                    persist_dir = "/Users/xaa/zuoye/oneform/kuokka add"
                    token_path = os.path.join(persist_dir, "token.txt")
                    with open(token_path, "w") as f:
                        f.write(auth_header)
                    print(f"Saved token to {token_path}")
                    break
                    
        except Exception as e:
            print("Error receiving:", e)
            break
            
    ws.close()
    
    if token:
        print("Token successfully captured!")
    else:
        print("Could not capture Authorization token.")

if __name__ == "__main__":
    main()
