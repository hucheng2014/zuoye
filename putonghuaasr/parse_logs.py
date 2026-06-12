import json

log_path = "/Users/xaa/.gemini/antigravity-cli/brain/6ffe4535-d43d-47de-bd8b-27434df1d17f/.system_generated/logs/transcript.jsonl"

with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            data = json.loads(line)
            # Check if this is a USER_INPUT or has model content mentioning "模型"
            if data.get("type") == "USER_INPUT":
                content = data.get("content", "")
                print(f"Step {data.get('step_index')} ({data.get('source')} - {data.get('type')}):")
                print(content.strip())
                print("-" * 80)
        except Exception as e:
            pass
