import json
import urllib.request
import os

def main():
    persist_dir = "/Users/xaa/zuoye/oneform/kuokka add"
    token_path = os.path.join(persist_dir, "token.txt")
    
    with open(token_path, "r") as f:
        token = f.read().strip()
        
    requests_path = os.path.join(persist_dir, "scilliance_requests.json")
    window_id = "ee1dd89e-bcbb-429f-9198-2048eec1cba8" 
    task_id = "eb3b1f0b-7349-4318-a6b8-a30dd0ea8775"   
    
    if os.path.exists(requests_path):
        try:
            with open(requests_path, "r") as f:
                reqs = json.load(f)
            for r in reqs:
                url = r.get("url", "")
                if "task-content" in url and "windowId=" in url:
                    import urllib.parse
                    parsed = urllib.parse.urlparse(url)
                    params = urllib.parse.parse_qs(parsed.query)
                    if 'windowId' in params:
                        window_id = params['windowId'][0]
                    break
        except Exception as e:
            print("Error parsing logs:", e)

    content_url = f"https://starshot.scilliance.com/task-content?windowId={window_id}"
    
    headers = {
        "Authorization": token,
        "Accept": "application/json"
    }
    
    print(f"Fetching task content from {content_url}...")
    req = urllib.request.Request(content_url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            content_data = json.loads(resp.read().decode('utf-8'))
            output_content_path = os.path.join(persist_dir, "task_content.json")
            with open(output_content_path, "w", encoding="utf-8") as out_f:
                json.dump(content_data, out_f, indent=2, ensure_ascii=False)
            print(f"Successfully saved task content to {output_content_path}")
            
            print("\nPotential task duration settings in content:")
            for k, v in content_data.items():
                kl = k.lower()
                if "time" in kl or "tpt" in kl or "dur" in kl or "limit" in kl:
                    print(f"- {k}: {v}")
            
            # Fetch extend using task ID from content data
            task_id = content_data.get("id", task_id)
            extend_url = f"https://starshot.scilliance.com/task-content/{task_id}/extend?windowId={window_id}"
            print(f"\nFetching task extend metadata from {extend_url}...")
            req_ext = urllib.request.Request(extend_url, headers=headers)
            with urllib.request.urlopen(req_ext) as resp_ext:
                extend_data = json.loads(resp_ext.read().decode('utf-8'))
                output_extend_path = os.path.join(persist_dir, "task_extend.json")
                with open(output_extend_path, "w", encoding="utf-8") as out_f:
                    json.dump(extend_data, out_f, indent=2, ensure_ascii=False)
                print(f"Successfully saved task extend to {output_extend_path}")
                
                print("\nPotential task duration settings in extend:")
                for k, v in extend_data.items():
                    kl = k.lower()
                    if "time" in kl or "tpt" in kl or "dur" in kl or "limit" in kl:
                        print(f"- {k}: {v}")
                        
    except Exception as e:
        print("Failed to fetch task content or extend:", e)

if __name__ == "__main__":
    main()
