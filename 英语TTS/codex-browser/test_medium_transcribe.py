from pathlib import Path

from faster_whisper import WhisperModel


AUDIO_DIR = Path(r"C:\Users\BERN7P\codex-browser\page_41239_audio")
FILES = [
    "20260127_00004314_zqbl_421_4.wav",
    "20260127_00004314_zqbl_421_1.wav",
    "20260127_00004314_zqbl_421_14.wav",
]


def main():
    model = WhisperModel("medium", device="cpu", compute_type="int8")
    prompt = "球鞋 缓震 场地 水泥 沥青 煤渣 塑胶 木板 IC 平底 骚客购"
    for name in FILES:
        audio_path = AUDIO_DIR / name
        segments, info = model.transcribe(
            str(audio_path),
            language="zh",
            beam_size=8,
            vad_filter=True,
            condition_on_previous_text=False,
            initial_prompt=prompt,
        )
        text = "".join(segment.text for segment in segments).strip()
        print(name)
        print(text)
        print(info.language, info.language_probability)
        print("---")


if __name__ == "__main__":
    main()
