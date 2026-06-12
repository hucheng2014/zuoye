from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import sys
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import funasr
import numpy as np
import torch
from funasr import AutoModel


DEFAULT_MODEL = os.getenv("APPEN_ASR_MODEL", "FunAudioLLM/Fun-ASR-Nano-2512")
DEFAULT_CACHE = Path(r"C:\Users\BERN7P\AppData\Local\Temp\edge_appen")
_MODEL = None


def register_funasr_nano() -> None:
    package_dir = Path(funasr.__file__).resolve().parent / "models" / "fun_asr_nano"
    if package_dir.exists():
        path_value = str(package_dir.resolve())
        if path_value not in sys.path:
            sys.path.insert(0, path_value)
        importlib.import_module("model")


def get_model():
    global _MODEL
    if _MODEL is None:
        register_funasr_nano()
        _MODEL = AutoModel(
            model=DEFAULT_MODEL,
            trust_remote_code=True,
            device="cpu",
            disable_update=True,
        )
    return _MODEL


def cache_audio_from_url(url: str, cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    suffix = Path(urllib.parse.urlparse(url).path).suffix or ".wav"
    out = cache_dir / f"{digest}{suffix}"
    if not out.exists():
        with urllib.request.urlopen(url, timeout=120) as resp, out.open("wb") as handle:
            handle.write(resp.read())
    return out


def read_wav_as_float32(audio_path: Path, target_sr: int = 16000) -> np.ndarray:
    with wave.open(str(audio_path), "rb") as handle:
        channels = handle.getnchannels()
        sample_width = handle.getsampwidth()
        sample_rate = handle.getframerate()
        frame_count = handle.getnframes()
        raw = handle.readframes(frame_count)

    if sample_width == 1:
        audio = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
        audio = (audio - 128.0) / 128.0
    elif sample_width == 2:
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif sample_width == 4:
        audio = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise RuntimeError(f"Unsupported WAV sample width: {sample_width} bytes")

    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)

    if sample_rate != target_sr and audio.size:
        duration = audio.shape[0] / sample_rate
        target_size = max(int(round(duration * target_sr)), 1)
        source_x = np.linspace(0.0, duration, num=audio.shape[0], endpoint=False)
        target_x = np.linspace(0.0, duration, num=target_size, endpoint=False)
        audio = np.interp(target_x, source_x, audio).astype(np.float32)

    return np.clip(audio.astype(np.float32), -1.0, 1.0)


def prepare_audio_input(audio_path: Path):
    if audio_path.suffix.lower() == ".wav":
        return torch.from_numpy(read_wav_as_float32(audio_path))
    return str(audio_path)


def transcribe(audio_path: Path) -> dict:
    model = get_model()
    audio_input = prepare_audio_input(audio_path)
    result = model.generate(input=audio_input)
    item = result[0] if isinstance(result, list) and result else {"text": "", "raw": result}
    return {
        "audioPath": str(audio_path),
        "text": str(item.get("text", "")).strip(),
        "raw": item,
        "model": DEFAULT_MODEL,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio-file", type=Path)
    parser.add_argument("--audio-url")
    parser.add_argument("--warmup", action="store_true")
    args = parser.parse_args()

    if args.warmup:
        model = get_model()
        print(
            json.dumps(
                {"ok": True, "model": DEFAULT_MODEL, "modelPath": getattr(model, "model_path", None)},
                ensure_ascii=False,
            )
        )
        return

    if args.audio_file:
        audio_path = args.audio_file
    elif args.audio_url:
        audio_path = cache_audio_from_url(args.audio_url, DEFAULT_CACHE)
    else:
        raise SystemExit("Provide --audio-file or --audio-url or --warmup.")

    print(json.dumps(transcribe(audio_path), ensure_ascii=False))


if __name__ == "__main__":
    main()
