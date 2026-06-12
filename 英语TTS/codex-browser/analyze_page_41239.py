import json
from pathlib import Path
from difflib import SequenceMatcher

import librosa
import numpy as np
import requests
from faster_whisper import WhisperModel


PAGE_JSON = Path(r"C:\Users\BERN7P\codex-browser\page_41239.json")
AUDIO_DIR = Path(r"C:\Users\BERN7P\codex-browser\page_41239_audio")
OUT_JSON = Path(r"C:\Users\BERN7P\codex-browser\page_41239_analysis.json")


def normalize_text(text: str) -> str:
    text = text.replace(" ", "")
    text = text.replace("，", ",").replace("。", ".").replace("？", "?").replace("！", "!")
    text = text.replace("：", ":").replace("；", ";")
    text = text.replace("（", "(").replace("）", ")")
    text = text.replace("k", "K").replace("ｋ", "K")
    text = text.replace("今天的话", "今天的话").replace("i c", "IC").replace("ic", "IC")
    text = text.replace("內容", "内容").replace("對", "对").replace("幫助", "帮助")
    text = text.replace("裡", "里").replace("這種", "这种").replace("這", "这")
    return text.strip().lower()


def text_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()


def audio_features(audio_path: Path) -> dict:
    y, sr = librosa.load(audio_path, sr=16000, mono=True)
    if len(y) == 0:
        return {
            "rms_mean": 0.0,
            "rms_std": 0.0,
            "zcr_mean": 0.0,
            "centroid_mean": 0.0,
            "rolloff_mean": 0.0,
            "mfcc_mean": [0.0] * 13,
        }
    rms = librosa.feature.rms(y=y)[0]
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    return {
        "rms_mean": float(np.mean(rms)),
        "rms_std": float(np.std(rms)),
        "zcr_mean": float(np.mean(zcr)),
        "centroid_mean": float(np.mean(centroid)),
        "rolloff_mean": float(np.mean(rolloff)),
        "mfcc_mean": [float(x) for x in np.mean(mfcc, axis=1)],
    }


def mark_feature_outliers(items: list[dict]) -> list[dict]:
    if not items:
        return items
    keys = ["rms_mean", "rms_std", "zcr_mean", "centroid_mean", "rolloff_mean"]
    stats = {}
    for key in keys:
        values = np.array([item["audio_features"][key] for item in items], dtype=float)
        stats[key] = {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
        }
    for item in items:
        item["feature_zscores"] = {}
        for key in keys:
            std = stats[key]["std"]
            mean = stats[key]["mean"]
            value = item["audio_features"][key]
            zscore = 0.0 if std == 0 else abs((value - mean) / std)
            item["feature_zscores"][key] = float(zscore)
        item["is_feature_outlier"] = any(z > 2.5 for z in item["feature_zscores"].values())
    return items


def download_audio(items):
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    for item in items:
        target = AUDIO_DIR / item["filename"]
        if target.exists() and target.stat().st_size > 0:
            continue
        response = session.get(item["src"], timeout=60)
        response.raise_for_status()
        target.write_bytes(response.content)


def transcribe_items(items):
    model = WhisperModel("small", device="cpu", compute_type="int8")
    results = []
    for item in items:
        audio_path = AUDIO_DIR / item["filename"]
        segments, info = model.transcribe(
            str(audio_path),
            language="zh",
            beam_size=5,
            vad_filter=True,
        )
        transcript = "".join(segment.text for segment in segments).strip()
        expected = item["text"].strip()
        features = audio_features(audio_path)
        results.append(
            {
                "index": item["index"],
                "filename": item["filename"],
                "duration_page": item["duration"],
                "expected_text": expected,
                "whisper_text": transcript,
                "normalized_equal": normalize_text(expected) == normalize_text(transcript),
                "text_ratio": text_ratio(expected, transcript),
                "language": info.language,
                "language_probability": info.language_probability,
                "audio_features": features,
            }
        )
    return mark_feature_outliers(results)


def main():
    data = json.loads(PAGE_JSON.read_text(encoding="utf-8-sig"))
    items = data["items"]
    download_audio(items)
    analyses = transcribe_items(items)
    OUT_JSON.write_text(
        json.dumps(
            {
                "url": data["url"],
                "title": data["title"],
                "count": data["count"],
                "items": analyses,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(str(OUT_JSON))


if __name__ == "__main__":
    main()
