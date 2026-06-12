#!/usr/bin/env python3
"""
Local analysis using pre-downloaded models only (no network downloads).
Usage: python3 analyze_local.py --audio /tmp/audio.wav --task-type bridge --edit-start 4.4 --edit-end 9.2
"""
import argparse
import json
import sys
import numpy as np
import librosa

CLAP_MODEL = "/app/RQOAE/models/music_audioset_epoch_15_esc_90.14.pt"
PANNS_MODEL = "/root/panns_data/Cnn14_mAP=0.431.pth"


def analyze_with_panns(audio_path, edit_start, edit_end, sr=32000):
    from panns_inference import AudioTagging
    y, _ = librosa.load(audio_path, sr=sr, mono=True)
    duration = len(y) / sr

    start_sample = max(0, int(edit_start * sr))
    end_sample = min(len(y), int(edit_end * sr))
    edit_region = y[start_sample:end_sample]

    if len(edit_region) < sr * 0.1:
        return {"score": 1.0, "issues": ["edit_region_too_short"], "acoustic": {}}

    at = AudioTagging(checkpoint_path=PANNS_MODEL, device='cpu')
    edit_clip = edit_region[np.newaxis, :]
    tags, _ = at.inference(edit_clip)

    rms = float(np.sqrt(np.mean(edit_region**2)))
    silence_ratio = float(np.sum(np.abs(edit_region) < 0.01)) / len(edit_region)

    hop = 512
    rms_env = librosa.feature.rms(y=edit_region, hop_length=hop)[0]
    max_jump = float(np.max(np.abs(np.diff(rms_env)))) if len(rms_env) > 2 else 0.0
    avg_energy = float(np.mean(rms_env))

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


def analyze_with_clap(audio_path, task_type):
    import laion_clap
    model = laion_clap.CLAP_Module(enable_fusion=False, amodel='HTSAT-base')
    model.load_ckpt(ckpt=CLAP_MODEL)

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

    exp_sim = np.exp(similarities - np.max(similarities))
    probs = exp_sim / exp_sim.sum()

    clap_score = float(np.dot(probs, score_map))
    best_idx = int(np.argmax(similarities))

    return {
        "score": round(clap_score, 2),
        "best_match": quality_texts[best_idx],
        "confidence": round(float(probs[best_idx]), 3),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--task-type", required=True)
    parser.add_argument("--edit-start", type=float, required=True)
    parser.add_argument("--edit-end", type=float, required=True)
    args = parser.parse_args()

    print("Running PANNs analysis...", file=sys.stderr)
    try:
        panns_result = analyze_with_panns(args.audio, args.edit_start, args.edit_end)
    except Exception as e:
        panns_result = {"score": 3.0, "error": str(e)}
        print(f"PANNs error: {e}", file=sys.stderr)

    print("Running CLAP analysis...", file=sys.stderr)
    try:
        clap_result = analyze_with_clap(args.audio, args.task_type)
    except Exception as e:
        clap_result = {"score": 3.0, "error": str(e)}
        print(f"CLAP error: {e}", file=sys.stderr)

    combined = (clap_result["score"] + panns_result["score"]) / 2
    if abs(clap_result["score"] - panns_result["score"]) > 1.5:
        combined = panns_result["score"]

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
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
