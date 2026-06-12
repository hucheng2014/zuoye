import json
from pathlib import Path
from difflib import SequenceMatcher

import requests
from faster_whisper import WhisperModel


PAGE_JSON = Path(r"C:\Users\BERN7P\codex-browser\page_current.json")
AUDIO_DIR = Path(r"C:\Users\BERN7P\codex-browser\page_current_audio")
OUT_JSON = Path(r"C:\Users\BERN7P\codex-browser\page_current_medium_transcripts.json")
MODEL_DIR = Path(r"C:\Users\BERN7P\codex-browser\models\faster-whisper-medium")


def normalize_text(text: str) -> str:
    table = str.maketrans(
        {
            "，": ",",
            "。": ".",
            "？": "?",
            "！": "!",
            "：": ":",
            "；": ";",
            "（": "(",
            "）": ")",
            "“": '"',
            "”": '"',
            "‘": "'",
            "’": "'",
            " ": "",
        }
    )
    return text.translate(table).strip().lower()


def text_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()


def download_audio(items):
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    for item in items:
        target = AUDIO_DIR / item["filename"]
        if target.exists() and target.stat().st_size > 0:
            continue
        response = session.get(item["src"], timeout=120)
        response.raise_for_status()
        target.write_bytes(response.content)


def main() -> None:
    page = json.loads(PAGE_JSON.read_text(encoding="utf-8-sig"))
    items = page["items"]
    download_audio(items)

    model = WhisperModel(str(MODEL_DIR), device="cpu", compute_type="int8")
    prompt = "耐克 鬼牌 毒蜂 刺客 世界杯 配色 中端 顶级 超顶级 JP 二七零 二六五 终端 鞋圈 飞线 包裹性 缓震 袋鼠皮 牛皮 中底 鞋底 后跟 鞋面"
    rows = []
    for item in items:
        audio_path = AUDIO_DIR / item["filename"]
        segments, info = model.transcribe(
            str(audio_path),
            language="zh",
            beam_size=8,
            best_of=8,
            patience=1.2,
            vad_filter=True,
            condition_on_previous_text=False,
            initial_prompt=prompt,
            repetition_penalty=1.02,
        )
        transcript = "".join(segment.text for segment in segments).strip()
        rows.append(
            {
                "index": item["index"],
                "filename": item["filename"],
                "expected_text": item["text"],
                "medium_text": transcript,
                "ratio": round(text_ratio(item["text"], transcript), 4),
                "language": info.language,
                "language_probability": info.language_probability,
            }
        )

    OUT_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(OUT_JSON))


if __name__ == "__main__":
    main()
