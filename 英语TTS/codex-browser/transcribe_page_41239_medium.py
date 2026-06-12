import json
from pathlib import Path
from difflib import SequenceMatcher

from faster_whisper import WhisperModel


PAGE_JSON = Path(r"C:\Users\BERN7P\codex-browser\page_41239.json")
OUT_JSON = Path(r"C:\Users\BERN7P\codex-browser\page_41239_medium_transcripts.json")
AUDIO_DIR = Path(r"C:\Users\BERN7P\codex-browser\page_41239_audio")
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


def main() -> None:
    page = json.loads(PAGE_JSON.read_text(encoding="utf-8-sig"))
    # Keep the user-confirmed correction in sync during analysis.
    for item in page["items"]:
        if item["filename"] == "20260127_00004314_zqbl_421_4.wav":
            item["text"] = "比较常见的呢是一些这种水泥的场地，还有一些就是那种沥青和煤渣。"

    model = WhisperModel(str(MODEL_DIR), device="cpu", compute_type="int8")
    prompt = "老K IC 平底球鞋 场地 塑胶 木板 缓震 水泥 沥青 煤渣 骚客购 球鞋测评 选装备 平台"

    rows = []
    for item in page["items"]:
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
