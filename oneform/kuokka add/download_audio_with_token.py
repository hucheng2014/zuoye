import os
import urllib.request

def main():
    persist_dir = "/Users/xaa/zuoye/oneform/kuokka add"
    token_path = os.path.join(persist_dir, "token.txt")
    output_path = os.path.join(persist_dir, "task_audio.wav")
    
    with open(token_path, "r") as f:
        token = f.read().strip()
        
    wav_url = "https://assets-public.scilliance.com/89ff40213b40404fa60ada2ed2b96164/Kuokka/ms-MY/Dx-pT-bp/20260529/17681eb12d54068de8238384a4713f36.wav"
    
    print(f"Downloading audio from {wav_url}...")
    
    req = urllib.request.Request(wav_url)
    req.add_header("Authorization", token)
    
    try:
        with urllib.request.urlopen(req) as response:
            data = response.read()
            with open(output_path, "wb") as out_f:
                out_f.write(data)
            print(f"Successfully downloaded audio file to {output_path} ({len(data)} bytes)")
    except Exception as e:
        print("Failed to download audio:", e)

if __name__ == "__main__":
    main()
