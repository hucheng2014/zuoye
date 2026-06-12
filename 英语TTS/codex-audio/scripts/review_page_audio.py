import argparse
import json
import math
import os
import re
import statistics
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import librosa
import requests
from faster_whisper import WhisperModel
from huggingface_hub import snapshot_download
from transformers import pipeline


NOISE_MODEL_REPO = "Etherll/NoisySpeechDetection-v0.2"
DEFAULT_WHISPER_MODELS = {
    "large-v3": r"C:\Users\BERN7P\codex-browser\models\faster-whisper-large-v3",
    "medium": r"C:\Users\BERN7P\codex-browser\models\faster-whisper-medium",
}
CUT_TEXT_ENDINGS = {
    "的",
    "了",
    "呢",
    "啊",
    "呀",
    "吧",
    "嘛",
    "么",
    "是",
    "还",
    "就",
    "有",
    "没",
    "在",
    "和",
    "跟",
    "比",
    "到",
    "向",
}


@dataclass
class TranscriptResult:
    model_name: str
    text: str
    avg_logprob: float | None
    no_speech_prob: float | None
    duration: float | None
    language: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Review an iLabel page snapshot with noise classification and multi-model ASR.",
    )
    parser.add_argument("--snapshot", required=True, help="Path to extracted page snapshot JSON.")
    parser.add_argument(
        "--audio-dir",
        help="Directory for downloaded audio. Defaults to a folder next to the snapshot.",
    )
    parser.add_argument(
        "--output-prefix",
        help="Prefix for generated JSON/MD reports. Defaults to next to the snapshot.",
    )
    parser.add_argument(
        "--noise-threshold",
        type=float,
        default=0.20,
        help="Threshold for noisy=yes. Sliding-window max score is used.",
    )
    parser.add_argument(
        "--window-seconds",
        type=float,
        default=2.5,
        help="Window size for noise classification.",
    )
    parser.add_argument(
        "--stride-seconds",
        type=float,
        default=1.0,
        help="Stride for noise classification windows.",
    )
    parser.add_argument(
        "--download-timeout",
        type=int,
        default=120,
        help="Timeout in seconds for audio downloads.",
    )
    parser.add_argument(
        "--progress-file",
        help="Optional JSON file updated after each reviewed item.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_progress(
    progress_path: Path | None,
    *,
    status: str,
    total: int,
    completed: int,
    current_filename: str | None = None,
    output_prefix: Path | None = None,
) -> None:
    if progress_path is None:
        return
    payload = {
        "status": status,
        "total": total,
        "completed": completed,
        "remaining": max(total - completed, 0),
        "percent": round((completed / total) * 100, 2) if total else 100.0,
        "current_filename": current_filename,
        "output_prefix": str(output_prefix) if output_prefix is not None else None,
    }
    write_json(progress_path, payload)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").strip().lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[，。！？、；：,.!?;:\"'“”‘’\-\(\)\[\]<>《》/\\]+", "", text)
    return text


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()


def terminal_text_char(text: str) -> str:
    cleaned = re.sub(r"[，。！？、；：,.!?;:\"'“”‘’\s]+$", "", text or "")
    return cleaned[-1:] if cleaned else ""


def compare_text_shapes(page_text: str, consensus_text: str) -> dict[str, Any]:
    page_norm = normalize_text(page_text)
    consensus_norm = normalize_text(consensus_text)
    matcher = SequenceMatcher(None, page_norm, consensus_norm)

    deleted_chunks: list[str] = []
    inserted_chunks: list[str] = []
    replaced_pairs: list[tuple[str, str]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "delete":
            deleted_chunks.append(page_norm[i1:i2])
        elif tag == "insert":
            inserted_chunks.append(consensus_norm[j1:j2])
        elif tag == "replace":
            replaced_pairs.append((page_norm[i1:i2], consensus_norm[j1:j2]))

    deleted_len = sum(len(x) for x in deleted_chunks)
    inserted_len = sum(len(x) for x in inserted_chunks)
    replace_delta = sum(max(len(a), len(b)) for a, b in replaced_pairs)
    is_small_delete_only = deleted_len > 0 and inserted_len == 0 and replace_delta == 0 and deleted_len <= 2
    has_tail_overhang = False
    if page_norm and consensus_norm and page_norm.startswith(consensus_norm):
        extra = page_norm[len(consensus_norm) :]
        has_tail_overhang = 0 < len(extra) <= 2

    return {
        "deleted_chunks": deleted_chunks,
        "inserted_chunks": inserted_chunks,
        "replaced_pairs": replaced_pairs,
        "deleted_len": deleted_len,
        "inserted_len": inserted_len,
        "replace_delta": replace_delta,
        "is_small_delete_only": is_small_delete_only,
        "has_tail_overhang": has_tail_overhang,
    }


def ensure_audio_dir(snapshot_path: Path, audio_dir_arg: str | None) -> Path:
    if audio_dir_arg:
        path = Path(audio_dir_arg)
    else:
        path = snapshot_path.with_suffix("")
        path = path.parent / f"{path.name}_audio"
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_output_prefix(snapshot_path: Path, output_prefix_arg: str | None) -> Path:
    if output_prefix_arg:
        return Path(output_prefix_arg)
    stem = snapshot_path.stem
    return snapshot_path.parent / f"{stem}_review"


def download_audio(url: str, dest: Path, timeout_seconds: int) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    dest.write_bytes(response.content)


def resolve_noise_model_path() -> str:
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    try:
        return snapshot_download(NOISE_MODEL_REPO, local_files_only=True)
    except Exception:
        return snapshot_download(NOISE_MODEL_REPO)


def score_to_map(scores: list[dict[str, float | str]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for row in scores:
        label = str(row["label"])
        out[label] = float(row["score"])
    return out


def build_noise_windows(wave: Any, sample_rate: int, window_seconds: float, stride_seconds: float) -> list[tuple[float, Any]]:
    total_samples = len(wave)
    if total_samples == 0:
        return [(0.0, wave)]

    window_size = max(1, int(window_seconds * sample_rate))
    stride_size = max(1, int(stride_seconds * sample_rate))

    if total_samples <= window_size:
        return [(0.0, wave)]

    windows: list[tuple[float, Any]] = []
    start = 0
    while start + window_size <= total_samples:
        windows.append((start / sample_rate, wave[start : start + window_size]))
        start += stride_size

    if windows:
        last_start = total_samples - window_size
        if last_start / sample_rate > windows[-1][0]:
            windows.append((last_start / sample_rate, wave[last_start:total_samples]))
    return windows


def classify_noise(
    classifier: Any,
    audio_path: Path,
    window_seconds: float,
    stride_seconds: float,
) -> dict[str, Any]:
    wave, sample_rate = librosa.load(str(audio_path), sr=16000, mono=True)
    whole_scores = score_to_map(classifier(wave, top_k=None))

    windows = build_noise_windows(wave, sample_rate, window_seconds, stride_seconds)
    window_results: list[dict[str, Any]] = []
    for start_seconds, chunk in windows:
        chunk_scores = score_to_map(classifier(chunk, top_k=None))
        window_results.append(
            {
                "start_seconds": round(start_seconds, 3),
                "clean": round(chunk_scores.get("clean", 0.0), 6),
                "noisy": round(chunk_scores.get("noisy", 0.0), 6),
            }
        )

    max_window = max((row["noisy"] for row in window_results), default=0.0)
    return {
        "whole": {
            "clean": round(whole_scores.get("clean", 0.0), 6),
            "noisy": round(whole_scores.get("noisy", 0.0), 6),
        },
        "max_window_noisy": round(max_window, 6),
        "window_seconds": window_seconds,
        "stride_seconds": stride_seconds,
        "windows": window_results,
    }


def analyze_audio_ending(audio_path: Path) -> dict[str, Any]:
    wave, sample_rate = librosa.load(str(audio_path), sr=16000, mono=True)
    if len(wave) == 0:
        return {
            "duration_seconds": 0.0,
            "tail_silence_seconds": 0.0,
            "overall_rms": 0.0,
            "end_rms": 0.0,
            "end_peak": 0.0,
            "end_rms_ratio": 0.0,
            "speech_reaches_file_end": False,
        }

    frame_length = 512
    hop_length = 128
    rms = librosa.feature.rms(y=wave, frame_length=frame_length, hop_length=hop_length)[0]
    overall_rms = float(rms.mean()) if len(rms) else 0.0
    silence_threshold = max(overall_rms * 0.25, 0.0015)

    last_voiced_frame = -1
    for idx, value in enumerate(rms):
        if float(value) >= silence_threshold:
            last_voiced_frame = idx

    duration_seconds = len(wave) / sample_rate
    if last_voiced_frame >= 0:
        last_voiced_end = min(
            duration_seconds,
            ((last_voiced_frame * hop_length) + frame_length) / sample_rate,
        )
    else:
        last_voiced_end = 0.0

    tail_silence_seconds = max(0.0, duration_seconds - last_voiced_end)
    end_samples = max(1, int(sample_rate * 0.18))
    end_chunk = wave[-end_samples:]
    end_rms = math.sqrt(float((end_chunk**2).mean())) if len(end_chunk) else 0.0
    end_peak = float(abs(end_chunk).max()) if len(end_chunk) else 0.0
    end_rms_ratio = end_rms / overall_rms if overall_rms > 0 else 0.0

    return {
        "duration_seconds": round(duration_seconds, 3),
        "tail_silence_seconds": round(tail_silence_seconds, 3),
        "overall_rms": round(overall_rms, 6),
        "end_rms": round(end_rms, 6),
        "end_peak": round(end_peak, 6),
        "end_rms_ratio": round(end_rms_ratio, 6),
        "speech_reaches_file_end": tail_silence_seconds < 0.12,
    }


def load_whisper_models() -> dict[str, WhisperModel]:
    models: dict[str, WhisperModel] = {}
    for model_name, model_path in DEFAULT_WHISPER_MODELS.items():
        models[model_name] = WhisperModel(model_path, device="cpu", compute_type="int8")
    return models


def transcribe_audio(model_name: str, model: WhisperModel, audio_path: Path) -> TranscriptResult:
    segments, info = model.transcribe(
        str(audio_path),
        language="zh",
        beam_size=5,
        best_of=5,
        vad_filter=True,
        condition_on_previous_text=False,
        word_timestamps=False,
    )

    texts: list[str] = []
    avg_logprobs: list[float] = []
    no_speech_probs: list[float] = []
    for seg in segments:
        texts.append(seg.text.strip())
        if getattr(seg, "avg_logprob", None) is not None:
            avg_logprobs.append(float(seg.avg_logprob))
        if getattr(seg, "no_speech_prob", None) is not None:
            no_speech_probs.append(float(seg.no_speech_prob))

    text = "".join(part for part in texts if part)
    return TranscriptResult(
        model_name=model_name,
        text=text,
        avg_logprob=statistics.fmean(avg_logprobs) if avg_logprobs else None,
        no_speech_prob=statistics.fmean(no_speech_probs) if no_speech_probs else None,
        duration=float(info.duration) if getattr(info, "duration", None) is not None else None,
        language=getattr(info, "language", None),
    )


def choose_consensus(page_text: str, transcripts: list[TranscriptResult]) -> dict[str, Any]:
    rows = []
    for row in transcripts:
        rows.append(
            {
                "model_name": row.model_name,
                "text": row.text,
                "similarity_to_page": round(similarity(page_text, row.text), 4),
                "avg_logprob": row.avg_logprob,
                "no_speech_prob": row.no_speech_prob,
            }
        )

    if not transcripts:
        return {"text": "", "source": "none", "rows": rows, "agreement": 0.0}

    if len(transcripts) == 1:
        return {
            "text": transcripts[0].text,
            "source": transcripts[0].model_name,
            "rows": rows,
            "agreement": 1.0,
        }

    left, right = transcripts[0], transcripts[1]
    agreement = similarity(left.text, right.text)

    chosen = left
    if agreement >= 0.90:
        if len(normalize_text(right.text)) > len(normalize_text(left.text)):
            chosen = right
        elif (right.avg_logprob or -999.0) > (left.avg_logprob or -999.0):
            chosen = right
        source = f"agree:{chosen.model_name}"
    else:
        left_page = similarity(page_text, left.text)
        right_page = similarity(page_text, right.text)
        if right_page > left_page + 0.03:
            chosen = right
        elif math.isclose(right_page, left_page, abs_tol=0.03) and (right.avg_logprob or -999.0) > (left.avg_logprob or -999.0):
            chosen = right
        source = chosen.model_name

    return {
        "text": chosen.text,
        "source": source,
        "rows": rows,
        "agreement": round(agreement, 4),
    }


def should_suggest_text(page_text: str, consensus_text: str, agreement: float) -> bool:
    if not consensus_text:
        return False
    shape = compare_text_shapes(page_text, consensus_text)
    page_vs_consensus = similarity(page_text, consensus_text)
    if agreement >= 0.90 and shape["deleted_len"] > 0 and shape["inserted_len"] == 0 and shape["replace_delta"] <= 1:
        return True
    if agreement >= 0.78 and (shape["has_tail_overhang"] or shape["is_small_delete_only"]):
        return True
    if agreement >= 0.90 and page_vs_consensus < 0.92:
        return True
    if agreement >= 0.84 and page_vs_consensus < 0.82:
        return True
    return False


def text_review_hint(shape: dict[str, Any], agreement: float, page_vs_consensus: float) -> dict[str, Any]:
    score = 0.0
    reasons: list[str] = []

    if shape["deleted_len"] > 0 and shape["inserted_len"] == 0:
        score += 0.25
        reasons.append("page_has_extra_chars")
        if shape["deleted_len"] <= 2:
            score += 0.15
            reasons.append("extra_chars_count_le_2")

    if shape["has_tail_overhang"]:
        score += 0.2
        reasons.append("tail_overhang")

    if agreement >= 0.90:
        score += 0.25
        reasons.append("high_model_agreement")
    elif agreement >= 0.78:
        score += 0.12
        reasons.append("medium_model_agreement")

    if page_vs_consensus >= 0.94:
        score += 0.1
        reasons.append("high_similarity_despite_deletion")

    return {
        "score": round(min(score, 1.0), 4),
        "needs_manual_review": score >= 0.35,
        "reasons": reasons,
    }


def cut_review_hint(
    ending: dict[str, Any],
    page_text: str,
    consensus_text: str,
    shape: dict[str, Any],
) -> dict[str, Any]:
    score = 0.0
    reasons: list[str] = []

    tail_silence = float(ending["tail_silence_seconds"])
    end_peak = float(ending["end_peak"])
    end_rms_ratio = float(ending["end_rms_ratio"])

    if tail_silence < 0.05:
        score += 0.32
        reasons.append("tail_silence_lt_50ms")
    elif tail_silence < 0.09:
        score += 0.2
        reasons.append("tail_silence_lt_90ms")
    elif tail_silence < 0.13:
        score += 0.1
        reasons.append("tail_silence_lt_130ms")

    if end_peak > 0.25:
        score += 0.22
        reasons.append("high_end_peak")
    elif end_peak > 0.12:
        score += 0.12
        reasons.append("medium_end_peak")

    if end_rms_ratio > 0.9:
        score += 0.22
        reasons.append("high_end_rms_ratio")
    elif end_rms_ratio > 0.55:
        score += 0.12
        reasons.append("medium_end_rms_ratio")

    end_char = terminal_text_char(consensus_text or page_text)
    if end_char and end_char in CUT_TEXT_ENDINGS:
        score += 0.12
        reasons.append(f"text_ends_with_{end_char}")

    if shape["has_tail_overhang"]:
        score += 0.18
        reasons.append("page_has_tail_overhang")

    if shape["is_small_delete_only"]:
        score += 0.08
        reasons.append("small_delete_only_diff")

    return {
        "score": round(min(score, 1.0), 4),
        "needs_manual_review": score >= 0.38,
        "reasons": reasons,
    }


def make_markdown(report: dict[str, Any]) -> str:
    lines = []
    lines.append(f"# Page Review")
    lines.append("")
    lines.append(f"- Snapshot: `{report['snapshot_path']}`")
    lines.append(f"- Audio dir: `{report['audio_dir']}`")
    lines.append(f"- Item count: `{report['count']}`")
    lines.append(f"- Noise threshold: `{report['noise_threshold']}`")
    lines.append("")

    for item in report["items"]:
        lines.append(f"## {item['filename']}")
        lines.append("")
        lines.append(f"- Page noise selected: `{item['page_noise_selected']}`")
        lines.append(f"- Noise score whole/max-window: `{item['noise']['whole']['noisy']}` / `{item['noise']['max_window_noisy']}`")
        lines.append(f"- Suggested noise: `{item['noise_suggestion']}`")
        lines.append(f"- Cut review hint: `{item['cut_review_hint']['score']}` reasons=`{','.join(item['cut_review_hint']['reasons'])}`")
        lines.append(f"- Ending metrics: tail_sil=`{item['ending']['tail_silence_seconds']}` end_peak=`{item['ending']['end_peak']}` end_rms_ratio=`{item['ending']['end_rms_ratio']}`")
        lines.append(f"- Page text similarity to consensus: `{item['similarity_page_vs_consensus']}`")
        lines.append(f"- Transcript agreement: `{item['transcript_consensus']['agreement']}`")
        lines.append(f"- Suggested text change: `{item['text_change_suggested']}`")
        lines.append(f"- Text review hint: `{item['text_review_hint']['score']}` reasons=`{','.join(item['text_review_hint']['reasons'])}`")
        lines.append(f"- Text shape: overhang=`{item['text_shape']['has_tail_overhang']}` small_delete_only=`{item['text_shape']['is_small_delete_only']}` deleted=`{item['text_shape']['deleted_chunks']}`")
        lines.append(f"- Page text: `{item['page_text']}`")
        lines.append(f"- Consensus text: `{item['transcript_consensus']['text']}`")
        for row in item["transcript_consensus"]["rows"]:
            lines.append(
                f"- {row['model_name']}: sim_to_page=`{row['similarity_to_page']}` avg_logprob=`{row['avg_logprob']}` text=`{row['text']}`"
            )
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    snapshot_path = Path(args.snapshot)
    snapshot = load_json(snapshot_path)
    progress_path = Path(args.progress_file) if args.progress_file else None

    audio_dir = ensure_audio_dir(snapshot_path, args.audio_dir)
    output_prefix = ensure_output_prefix(snapshot_path, args.output_prefix)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    if progress_path is not None:
        progress_path.parent.mkdir(parents=True, exist_ok=True)

    total_items = sum(1 for item in snapshot["items"] if item.get("filename"))
    write_progress(
        progress_path,
        status="starting",
        total=total_items,
        completed=0,
        output_prefix=output_prefix,
    )

    model_path = resolve_noise_model_path()
    noise_classifier = pipeline("audio-classification", model=model_path)
    whisper_models = load_whisper_models()

    items_out: list[dict[str, Any]] = []
    completed = 0
    for item in snapshot["items"]:
        filename = item["filename"]
        if not filename:
            continue

        write_progress(
            progress_path,
            status="reviewing",
            total=total_items,
            completed=completed,
            current_filename=filename,
            output_prefix=output_prefix,
        )

        audio_path = audio_dir / filename
        download_audio(item["src"], audio_path, timeout_seconds=args.download_timeout)

        noise_result = classify_noise(
            noise_classifier,
            audio_path,
            window_seconds=args.window_seconds,
            stride_seconds=args.stride_seconds,
        )
        ending_result = analyze_audio_ending(audio_path)
        noisy_score = max(
            float(noise_result["whole"]["noisy"]),
            float(noise_result["max_window_noisy"]),
        )
        noise_suggestion = "yes" if noisy_score >= args.noise_threshold else "no"

        transcripts = [
            transcribe_audio(model_name, model, audio_path)
            for model_name, model in whisper_models.items()
        ]
        consensus = choose_consensus(item.get("text", ""), transcripts)
        text_shape = compare_text_shapes(item.get("text", ""), consensus["text"])
        text_hint = text_review_hint(
            text_shape,
            float(consensus["agreement"]),
            similarity(item.get("text", ""), consensus["text"]),
        )
        text_change_suggested = should_suggest_text(
            item.get("text", ""),
            consensus["text"],
            float(consensus["agreement"]),
        )
        cut_hint = cut_review_hint(
            ending_result,
            item.get("text", ""),
            consensus["text"],
            text_shape,
        )

        page_noise_index = None
        selected_indexes = item.get("selectedIndexes") or []
        if len(selected_indexes) >= 5:
            page_noise_index = selected_indexes[4]

        items_out.append(
            {
                "filename": filename,
                "audio_path": str(audio_path),
                "page_text": item.get("text", ""),
                "page_selected_indexes": selected_indexes,
                "page_noise_selected": page_noise_index,
                "noise": noise_result,
                "ending": ending_result,
                "noise_score": round(noisy_score, 6),
                "noise_suggestion": noise_suggestion,
                "transcript_consensus": consensus,
                "text_shape": text_shape,
                "text_review_hint": text_hint,
                "cut_review_hint": cut_hint,
                "similarity_page_vs_consensus": round(
                    similarity(item.get("text", ""), consensus["text"]),
                    4,
                ),
                "text_change_suggested": text_change_suggested,
            }
        )
        completed += 1
        write_progress(
            progress_path,
            status="reviewing",
            total=total_items,
            completed=completed,
            current_filename=filename,
            output_prefix=output_prefix,
        )

    report = {
        "snapshot_path": str(snapshot_path),
        "audio_dir": str(audio_dir),
        "output_prefix": str(output_prefix),
        "url": snapshot.get("url"),
        "title": snapshot.get("title"),
        "count": len(items_out),
        "noise_model": NOISE_MODEL_REPO,
        "whisper_models": DEFAULT_WHISPER_MODELS,
        "noise_threshold": args.noise_threshold,
        "window_seconds": args.window_seconds,
        "stride_seconds": args.stride_seconds,
        "items": items_out,
    }

    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    write_json(json_path, report)
    md_path.write_text(make_markdown(report), encoding="utf-8")
    write_progress(
        progress_path,
        status="completed",
        total=total_items,
        completed=completed,
        output_prefix=output_prefix,
    )

    print(json.dumps({"json": str(json_path), "md": str(md_path), "count": len(items_out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
