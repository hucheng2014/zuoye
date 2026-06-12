import json
import urllib.request
import base64
import sys
import os
from websocket import create_connection

def main():
    ports = [9233, 9232]
    pages = None
    
    for port in ports:
        cdp_url = f"http://127.0.0.1:{port}"
        try:
            req = urllib.request.Request(f"{cdp_url}/json/list")
            with urllib.request.urlopen(req, timeout=5) as resp:
                pages = json.loads(resp.read())
                break
        except Exception:
            pass
            
    if not pages:
        print("Error: Could not connect to CDP.")
        sys.exit(1)
        
    page = [p for p in pages if p.get('type') == 'page' and "Annotation Tool" in p.get('title', '')][0]
    ws_url = page['webSocketDebuggerUrl']
    ws = create_connection(ws_url, timeout=30)
    
    ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
    ws.recv()
    
    def evaluate(js_expr):
        payload = {
            "id": 100,
            "method": "Runtime.evaluate",
            "params": {
                "expression": js_expr,
                "returnByValue": True,
                "awaitPromise": True
            }
        }
        ws.send(json.dumps(payload))
        while True:
            raw = ws.recv()
            data = json.loads(raw)
            if data.get("id") == 100:
                res = data.get("result", {})
                if "exceptionDetails" in res:
                    print("JS Error:", res["exceptionDetails"])
                    return None
                return res.get("result", {}).get("value")
                
    wav_url = "https://assets-public.scilliance.com/89ff40213b40404fa60ada2ed2b96164/Kuokka/ms-MY/Dx-pT-bp/20260529/17681eb12d54068de8238384a4713f36.wav"
    
    print(f"Fetching audio bytes via iframe window fetch from {wav_url}...")
    fetch_js = """
    (async () => {
        try {
            let iframe = document.querySelector('iframe');
            if (!iframe) return JSON.stringify({ error: "Iframe not found" });
            let win = iframe.contentWindow;
            
            // Execute fetch in the context of the iframe window
            let r = await win.fetch("WAV_URL_PLACEHOLDER", { credentials: 'include' });
            if (!r.ok) return JSON.stringify({ error: "HTTP error: " + r.status });
            
            let buffer = await r.arrayBuffer();
            let binary = '';
            let bytes = new Uint8Array(buffer);
            let len = bytes.byteLength;
            for (let i = 0; i < len; i++) {
                binary += String.fromCharCode(bytes[i]);
            }
            return JSON.stringify({ success: true, size: len, data: window.btoa(binary) });
        } catch(e) {
            return JSON.stringify({ error: e.message });
        }
    })()
    """.replace("WAV_URL_PLACEHOLDER", wav_url)
    
    result_str = evaluate(fetch_js)
    if result_str:
        result = json.loads(result_str)
        if "success" in result:
            persist_dir = "/Users/xaa/zuoye/oneform/kuokka add"
            output_path = os.path.join(persist_dir, "task_audio.wav")
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(result.get("data")))
            print(f"Successfully downloaded audio file to {output_path} (size: {result.get('size')} bytes)")
        else:
            print("Error downloading audio:", result.get("error"))
    else:
        print("Fetch script returned empty.")
        
    ws.close()

if __name__ == "__main__":
    main()
