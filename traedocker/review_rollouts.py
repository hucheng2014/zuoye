#!/usr/bin/env python3
"""Local rule review for Trae rollout logs before Bitable submission."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

from bitable_score_reason import is_generic_score_reason


BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "trial_log.csv"
TRAE_LOG_DIR = Path("/Users/xaa/.config/Trae CN/logs")

MODEL_IDS = {
    "Doubao-Seed-2.0-Code": "1_-_Doubao-Seed-2.0-Code",
    "GPT-5.4": "1_-_gpt-5.4",
    "Gemini 3.1 pro": "1_-_gemini-3.1-p",
    "DeepSeek-v4": "1_-_DeepSeek-V4-Pro",
    "MinMax-M2.7": "1_-_minimax-m2.7",
    "GLM-5.1": "1_-_glm-5.1",
    "Qwen3.6-Plus": "1_-_qwen-3.6-plus",
}

LOG_MODEL_IDS = {
    "Doubao-Seed-2.0-Code": "1_-_Doubao-Seed-2.0-Code",
    "doubao-seed-2.0-code": "1_-_Doubao-Seed-2.0-Code",
    "gpt-5.4": "1_-_gpt-5.4",
    "GPT-5.4": "1_-_gpt-5.4",
    "Gemini 3.1 pro": "1_-_gemini-3.1-p",
    "gemini-3.1-p": "1_-_gemini-3.1-p",
    "DeepSeek-v4": "1_-_DeepSeek-V4-Pro",
    "DeepSeek-V4-Pro": "1_-_DeepSeek-V4-Pro",
    "MinMax-M2.7": "1_-_minimax-m2.7",
    "MiniMax-M2.7": "1_-_minimax-m2.7",
    "minimax-m2.7": "1_-_minimax-m2.7",
    "GLM-5.1": "1_-_glm-5.1",
    "glm-5.1": "1_-_glm-5.1",
    "Qwen3.6-Plus": "1_-_qwen-3.6-plus",
    "qwen-3.6-plus": "1_-_qwen-3.6-plus",
}


def rollout5(prompt: int) -> str:
    return {
        0: "MinMax-M2.7",
        1: "GLM-5.1",
        2: "Qwen3.6-Plus",
    }[(prompt - 1) % 3]


def expected_models(prompt: int) -> list[str]:
    return [
        "Doubao-Seed-2.0-Code",
        "GPT-5.4",
        "Gemini 3.1 pro",
        "DeepSeek-v4",
        rollout5(prompt),
    ]


def load_rows(artifact_dir: Path = BASE_DIR) -> list[dict[str, str]]:
    log_file = artifact_dir / "trial_log.csv"
    if not log_file.exists():
        raise SystemExit(f"missing rollout log: {log_file}")
    with log_file.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"prompt", "model", "session_id", "score", "score_reason", "patch_file"}
    if not rows:
        raise SystemExit("trial_log.csv has no rollout rows")
    if set(rows[0]) != required:
        raise SystemExit(f"unexpected trial_log.csv columns: {sorted(rows[0])}")
    return rows


def normalize_log_model(model: str) -> str | None:
    if model in LOG_MODEL_IDS:
        return LOG_MODEL_IDS[model]
    key = model.strip().replace(" ", "-")
    return LOG_MODEL_IDS.get(key) or LOG_MODEL_IDS.get(key.lower())


def load_log_model_evidence() -> dict[str, str]:
    evidence: dict[str, str] = {}
    if not TRAE_LOG_DIR.exists():
        return evidence
    files = sorted(
        [
            path
            for path in TRAE_LOG_DIR.rglob("*.log")
            if path.name == "renderer.log" or path.name.startswith("ai-agent")
        ],
        key=lambda path: path.stat().st_mtime,
    )
    pattern = re.compile(r"params:\s+(\{.*\})")
    sid_pattern = re.compile(r"\b[0-9a-f]{24}\b")
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line in text.splitlines():
            if "chat_model" not in line:
                continue
            sids = sid_pattern.findall(line)
            if not sids:
                continue
            for match in pattern.finditer(line):
                try:
                    payload = json.loads(match.group(1))
                except Exception:
                    continue
                model_id = normalize_log_model(str(payload.get("chat_model", "")))
                if not model_id:
                    continue
                for sid in sids:
                    evidence[sid] = model_id
    return evidence


def load_log_session_status() -> dict[str, str]:
    status: dict[str, str] = {}
    if not TRAE_LOG_DIR.exists():
        return status
    files = sorted(
        [
            path
            for path in TRAE_LOG_DIR.rglob("*.log")
            if path.name == "renderer.log" or path.name.startswith("ai-agent")
        ],
        key=lambda path: path.stat().st_mtime,
    )
    sid_pattern = re.compile(r"\b[0-9a-f]{24}\b")
    completed_needles = (
        "code_comp_complete_shown",
        "reason=completed",
        "status=Completed",
    )
    error_needles = (
        "reason=error",
        "reason=user_stopped",
        "status=Failed",
        "status=Cancelled",
    )
    started_needles = (
        "chat_model",
        "code_comp_trigger",
        "tool_call_show",
        "file_tool_show",
        "run_script_show",
        "process_task",
        "do_chat",
    )
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line in text.splitlines():
            sids = sid_pattern.findall(line)
            if not sids:
                continue
            next_status = None
            if any(needle in line for needle in completed_needles):
                next_status = "completed"
            elif any(needle in line for needle in error_needles):
                next_status = "error"
            elif any(needle in line for needle in started_needles):
                next_status = "started"
            if not next_status:
                continue
            for sid in sids:
                if next_status == "completed" or sid not in status:
                    status[sid] = next_status
                elif next_status == "error" and status.get(sid) != "completed":
                    status[sid] = "error"
    return status


def review(artifact_dir: Path = BASE_DIR) -> int:
    rows = load_rows(artifact_dir)
    evidence = load_log_model_evidence()
    session_status = load_log_session_status()
    errors: list[str] = []
    warnings: list[str] = []

    if len(rows) != 35:
        errors.append(f"expected 35 rollout rows, found {len(rows)}")

    seen_sessions: set[str] = set()
    rows_by_prompt: dict[int, dict[str, dict[str, str]]] = {prompt: {} for prompt in range(1, 8)}
    session_re = re.compile(r"^[0-9a-f]{24}$")

    for index, row in enumerate(rows, 2):
        try:
            prompt = int(row["prompt"])
        except ValueError:
            errors.append(f"line {index}: invalid prompt index {row['prompt']!r}")
            continue
        model = row["model"]
        sid = row["session_id"]
        score = row["score"]
        reason = row["score_reason"].strip()
        patch_path = artifact_dir / row["patch_file"]

        if prompt not in rows_by_prompt:
            errors.append(f"line {index}: prompt must be 1..7, got {prompt}")
            continue
        if model in rows_by_prompt[prompt]:
            errors.append(f"line {index}: duplicate P{prompt} model {model}")
        rows_by_prompt[prompt][model] = row

        if not session_re.fullmatch(sid):
            errors.append(f"line {index}: invalid session_id {sid!r}")
        elif sid in seen_sessions:
            errors.append(f"line {index}: duplicate session_id {sid}")
        else:
            seen_sessions.add(sid)

        if score not in {"0", "1", "2"}:
            errors.append(f"line {index}: score must be 0/1/2, got {score!r}")
        if not reason:
            errors.append(f"line {index}: score_reason is empty")
        elif is_generic_score_reason(reason, prompt, model, score):
            errors.append(
                f"line {index}: score_reason still looks like auto template; "
                f"run: python3 bitable_score_reason.py normalize-log"
            )
        if not patch_path.exists():
            errors.append(f"line {index}: patch file missing: {patch_path.name}")
        elif patch_path.suffix != ".patch":
            errors.append(f"line {index}: patch file is not .patch: {patch_path.name}")
        elif prompt >= 2 and "diff --git " not in patch_path.read_text(encoding="utf-8", errors="ignore"):
            errors.append(f"line {index}: code-change prompt has empty patch: {patch_path.name}")

        expected_model_id = MODEL_IDS.get(model)
        actual_model_id = evidence.get(sid)
        if not actual_model_id:
            warnings.append(f"line {index}: no currently readable Trae chat_model log evidence for session {sid}")
        elif expected_model_id and actual_model_id != expected_model_id:
            errors.append(
                f"line {index}: model evidence mismatch for {sid}: "
                f"{actual_model_id} != {expected_model_id}"
            )
        if session_status.get(sid) != "completed":
            warnings.append(
                f"line {index}: no currently readable completed log evidence for session {sid} "
                f"(status={session_status.get(sid, 'absent')})"
            )

    for prompt in range(1, 8):
        expected = expected_models(prompt)
        actual = rows_by_prompt[prompt]
        missing = [model for model in expected if model not in actual]
        extra = [model for model in actual if model not in expected]
        if missing:
            errors.append(f"P{prompt}: missing model(s): {', '.join(missing)}")
        if extra:
            errors.append(f"P{prompt}: unexpected model(s): {', '.join(extra)}")

        if prompt >= 2:
            doubao = actual.get("Doubao-Seed-2.0-Code")
            if doubao and doubao["score"] != "0":
                errors.append(f"P{prompt}: Doubao seed score must be 0, got {doubao['score']}")
            scores = [row["score"] for row in actual.values()]
            if len(scores) == 5 and all(score == "2" for score in scores):
                errors.append(f"P{prompt}: non-reading prompt cannot have all five scores as 2")

        if prompt == 1:
            empty_patches = [
                row["patch_file"]
                for row in actual.values()
                if "diff --git " not in (artifact_dir / row["patch_file"]).read_text(
                    encoding="utf-8", errors="ignore"
                )
            ]
            if len(empty_patches) < 5:
                warnings.append("P1: explanation prompt produced code diffs for some models; review manually if unexpected")

    if errors:
        print("PRE-SUBMIT REVIEW FAILED")
        for item in errors:
            print(f"  [ERROR] {item}")
        for item in warnings:
            print(f"  [WARN] {item}")
        return 1

    print("PRE-SUBMIT REVIEW PASSED")
    print("  [OK] 35 rollout rows for 7 prompts")
    print("  [OK] each prompt has expected 5 models and unique sessions")
    print("  [OK] readable Trae chat_model evidence, when present, matches local model_name")
    print("  [OK] readable Trae completion evidence, when present, is accepted")
    print("  [OK] score_reason values are structured, not auto templates")
    print("  [OK] code-change prompts have non-empty .patch files")
    print("  [OK] Doubao seed score is 0 for prompts 2-7")
    print("  [OK] non-reading prompts are not all score 2")
    for item in warnings:
        print(f"  [WARN] {item}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local rule review for Trae rollout logs before Bitable submission.")
    parser.add_argument("--artifact-dir", type=Path, default=BASE_DIR)
    args = parser.parse_args()
    sys.exit(review(args.artifact_dir.resolve()))
