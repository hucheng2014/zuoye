#!/usr/bin/env python3
"""
RQOAE 音乐编辑质量分析 - 双模型（CLAP + PANNs）
用法: python3 analyze_audio_quality.py --url "音频URL" --task-type "intro" --edit-start 0 --edit-end 2
"""
import argparse
import json
import os
import sys
import tempfile
import urllib.request
import numpy as np
import librosa

CDP_ENDPOINT = os.environ.get("CDP_ENDPOINT", "http://browser:9223")

def get_cookies():
    """从浏览器获取认证 cookie"""
    from websocket import create_connection
    req = urllib.request.Request(f"{CDP_ENDPOINT}/json/list")
    req.add_header("Host", "localhost:9222")
    resp = urllib.request.urlopen(req, timeout=5)
    pages = json.loads(resp.read())
    if not pages:
        return ""
    ws_url = pages[0]["webSocketDebuggerUrl"].replace("ws://localhost:9222", "ws://browser:9223")
    ws = create_connection(ws_url, timeout=10, skip_utf8_validation=True)
    ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
    ws.settimeout(3)
    try:
        while True:
            r = ws.recv()
            if '"id"' in r: break
    except: pass
    ws.send(json.dumps({"id": 2, "method": "Network.getCookies", "params": {"urls": ["https://www.tryrating.com"]}}))
    ws.settimeout(5)
    cookies = ""
    try:
        while True:
            r = ws.recv()
            d = json.loads(r)
            if d.get("id") == 2:
                cookie_list = d.get("result", {}).get("cookies", [])
                cookies = "; ".join(f"{c['name']}={c['value']}" for c in cookie_list)
                break
    except: pass
    ws.close()
    return cookies

def download_audio(url, output_path):
    """带 cookie 下载音频"""
    cookies = get_cookies()
    req = urllib.request.Request(url)
    if cookies:
        req.add_header("Cookie", cookies)
    resp = urllib.request.urlopen(req, timeout=30)
    with open(output_path, "wb") as f:
        f.write(resp.read())
    return output_path

def analyze_with_clap(audio_path, task_type, edit_start, edit_end):
    """用 CLAP 模型分析音频质量"""
    import laion_clap
    model = laion_clap.CLAP_Module(enable_fusion=False, amodel='HTSAT-base')
    model.load_ckpt()
    
    quality_texts = [
        f"awful {task_type} with complete silence and empty audio",
        f"awful {task_type} with very abrupt cut and harsh distortion",
        f"poor {task_type} with unnatural timing and jarring transition",
        f"poor {task_type} with slight audio artifacts and clicks",
        f"average {task_type} with minor imperfections but passable quality",
        f"good {task_type} with smooth natural sounding music",
        f"excellent {task_type} with perfect seamless musical transition",
    ]
    score_map = [1.0, 1.0, 2.0, 2.0, 3.0, 4.0, 5.0]
    
    audio_embed = model.get_audio_embedding_from_filelist([audio_path])
    text_embed = model.get_text_embedding(quality_texts)
    similarities = (audio_embed @ text_embed.T).squeeze()
    
    # Softmax to get probabilities
    exp_sim = np.exp(similarities - np.max(similarities))
    probs = exp_sim / exp_sim.sum()
    
    clap_score = float(np.dot(probs, score_map))
    best_idx = int(np.argmax(similarities))
    
    return {
        "score": round(clap_score, 2),
        "best_match": quality_texts[best_idx],
        "confidence": round(float(probs[best_idx]), 3),
    }

def analyze_with_panns(audio_path, edit_start, edit_end, sr=32000):
    """用 PANNs + 声学特征分析"""
    from panns_inference import AudioTagging
    
    y, orig_sr = librosa.load(audio_path, sr=sr, mono=True)
    duration = len(y) / sr
    
    # Clamp edit region
    start_sample = max(0, int(edit_start * sr))
    end_sample = min(len(y), int(edit_end * sr))
    edit_region = y[start_sample:end_sample]
    
    if len(edit_region) < sr * 0.1:
        return {"score": 1.0, "issues": ["edit_region_too_short"], "acoustic": {}}
    
    # PANNs tagging
    at = AudioTagging(checkpoint_path=None, device='cpu')
    edit_clip = edit_region[np.newaxis, :]
    tags, _ = at.inference(edit_clip)
    
    # Acoustic features
    rms = float(np.sqrt(np.mean(edit_region**2)))
    silence_ratio = float(np.sum(np.abs(edit_region) < 0.01)) / len(edit_region)
    
    hop = 512
    rms_env = librosa.feature.rms(y=edit_region, hop_length=hop)[0]
    max_jump = float(np.max(np.abs(np.diff(rms_env)))) if len(rms_env) > 2 else 0.0
    avg_energy = float(np.mean(rms_env))
    
    # Issue detection
    issues = []
    if silence_ratio > 0.7:
        issues.append("mostly_silence")
    elif silence_ratio > 0.4:
        issues.append("partial_silence")
    if max_jump > 0.4:
        issues.append("very_abrupt")
    elif max_jump > 0.25:
        issues.append("somewhat_abrupt")
    if rms < 0.003:
        issues.append("near_silent")
    
    # Score
    score = 3.5
    if "mostly_silence" in issues or "near_silent" in issues:
        score = 1.0
    elif "partial_silence" in issues:
        score = 1.5
    elif "very_abrupt" in issues:
        score = 1.5
    elif "somewhat_abrupt" in issues:
        score = 2.5
    elif len(issues) == 0 and avg_energy > 0.02 and silence_ratio < 0.1:
        score = 4.0
    
    return {
        "score": round(score, 2),
        "issues": issues,
        "acoustic": {
            "rms": round(rms, 4),
            "silence_ratio": round(silence_ratio, 3),
            "max_energy_jump": round(max_jump, 4),
            "avg_energy": round(avg_energy, 4),
        },
        "duration": round(duration, 2),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--task-type", required=True)
    parser.add_argument("--edit-start", type=float, required=True)
    parser.add_argument("--edit-end", type=float, required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        audio_path = f.name
    
    print("Downloading audio (with auth)...", file=sys.stderr)
    download_audio(args.url, audio_path)
    
    # Verify it's actual audio
    file_size = os.path.getsize(audio_path)
    if file_size < 1000:
        with open(audio_path, 'r', errors='ignore') as f:
            content = f.read(200)
        if '<html' in content.lower():
            print("ERROR: Downloaded HTML instead of audio. Auth may have failed.", file=sys.stderr)
            os.unlink(audio_path)
            sys.exit(1)
    
    print(f"Audio file: {file_size} bytes", file=sys.stderr)
    print("Running PANNs analysis...", file=sys.stderr)
    try:
        panns_result = analyze_with_panns(audio_path, args.edit_start, args.edit_end)
    except Exception as e:
        panns_result = {"score": 3.0, "error": str(e)}
    
    print("Running CLAP analysis...", file=sys.stderr)
    try:
        clap_result = analyze_with_clap(audio_path, args.task_type, args.edit_start, args.edit_end)
    except Exception as e:
        clap_result = {"score": 3.0, "error": str(e)}
    
    # Combined
    combined = (clap_result["score"] + panns_result["score"]) / 2
    if abs(clap_result["score"] - panns_result["score"]) > 1.5:
        combined = panns_result["score"]  # trust acoustic analysis more
    
    rating_map = [(1.5, "Awful"), (2.5, "Poor"), (3.5, "Average"), (4.5, "Good"), (5.1, "Excellent")]
    rating = "Average"
    for threshold, label in rating_map:
        if combined <= threshold:
            rating = label
            break
    
    result = {
        "task_type": args.task_type,
        "edit": f"{args.edit_start}-{args.edit_end}s",
        "combined_score": round(combined, 2),
        "rating": rating,
        "clap": clap_result,
        "panns": panns_result,
    }
    
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
    print(output)
    os.unlink(audio_path)

if __name__ == "__main__":
    main()
