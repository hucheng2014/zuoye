import json
import os

# Generate mock data for rollouts
# 5 models for 7 prompts (Prompt 1 to 7)

models = [
    {"name": "Doubao-Seed-2.0-Code", "score": "0", "reason": "Failed to handle edge cases and database assertions were missing.", "session_prefix": "sess_doubao"},
    {"name": "GPT-5.4", "score": "5", "reason": "Perfect implementation, fully passed all unit tests and handled all constraints.", "session_prefix": "sess_gpt5"},
    {"name": "Gemini 3.1 pro", "score": "4", "reason": "Passed tests but code structure was slightly suboptimal in service layer.", "session_prefix": "sess_gemini"},
    {"name": "DeepSeek-v4", "score": "5", "reason": "Excellent code logic, well refactored and clear tests.", "session_prefix": "sess_deepseek"},
    {"name": "Qwen3.6-Plus", "score": "4", "reason": "Minor syntax issues in typing, but logic passed all core tests.", "session_prefix": "sess_qwen"}
]

rollouts = []

# Generate data for prompts 1 to 7
for p_idx in range(1, 8):
    for m_idx, model in enumerate(models):
        rollouts.append({
            "prompt_index": str(p_idx),
            "model_name": model["name"],
            "score": model["score"],
            "score_reason": model["reason"],
            "session_id": f"{model['session_prefix']}_{p_idx}_{m_idx}",
            "patch_file": f"prompt{p_idx}_{model['session_prefix']}.patch"
        })

with open("rollout_data.json", "w") as f:
    json.dump(rollouts, f, indent=4)

# Create dummy patch files
for r in rollouts:
    patch_path = r["patch_file"]
    if not os.path.exists(patch_path):
        with open(patch_path, "w") as f:
            f.write(f"# Dummy patch file for {r['model_name']} on Prompt {r['prompt_index']}\n")
            f.write("diff --git a/src/main.py b/src/main.py\n")

print(f"Generated {len(rollouts)} rollout records and dummy patch files.")
