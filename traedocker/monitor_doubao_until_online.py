#!/usr/bin/env python3
"""Read-only monitor for Doubao-Seed-2.0-Code availability state in Trae."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import time


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = Path.home() / ".config/Trae CN/logs"
WORKSPACE = "vscode-remote://ssh-remote%2Bodc-python-payment-container/app"
MODEL_NAME = "Doubao-Seed-2.0-Code"


def run(cmd: list[str], *, input_text: str | None = None, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=BASE_DIR,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def docker_repo_status() -> str:
    result = run(
        [
            "docker",
            "exec",
            "python-payment-container",
            "sh",
            "-lc",
            "cd /app && git status --short",
        ],
        timeout=20,
    )
    return result.stdout.strip()


def payloads_from_line(line: str) -> list[dict]:
    payloads: list[dict] = []
    for match in re.finditer(r"params:\s+(\{.*\})", line):
        try:
            payloads.append(json.loads(match.group(1)))
        except Exception:
            pass
    if "reportFrontResponse" in line:
        match = re.search(r"(\{.*\})", line)
        if match:
            try:
                payloads.append(json.loads(match.group(1)))
            except Exception:
                pass
    return payloads


def runtime_model_state() -> tuple[str, str]:
    """Classify Trae's latest observed chat mode from renderer telemetry."""
    if not LOG_DIR.exists():
        return "unknown", "Trae renderer logs not found"

    latest_auto: tuple[int, str] | None = None
    latest_target_manual: tuple[int, str] | None = None
    latest_other_manual: tuple[int, str] | None = None
    order = 0

    files = sorted(
        [p for p in LOG_DIR.rglob("renderer.log")],
        key=lambda p: (p.stat().st_mtime, str(p)),
    )
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            order += 1
            if "switch auto mode when model offline" in line:
                latest_auto = (order, f"{path}:{lineno}: switched to Auto after model offline")
                continue
            if (
                "model_select_click" not in line
                and "code_comp_trigger" not in line
                and "code_comp_shown" not in line
                and "code_comp_complete_shown" not in line
            ):
                continue
            for payload in payloads_from_line(line):
                model = payload.get("chat_model") or payload.get("model")
                mode = payload.get("chat_model_mode")
                is_auto = payload.get("is_auto_mode")
                if model == "auto" or mode == "auto" or is_auto == 1:
                    latest_auto = (order, f"{path}:{lineno}: Auto mode telemetry")
                elif mode == "manual" or is_auto == 0:
                    evidence = f"{path}:{lineno}: manual mode telemetry for {model or 'unknown model'}"
                    if model == MODEL_NAME:
                        latest_target_manual = (order, evidence)
                    else:
                        latest_other_manual = (order, evidence)

    if latest_target_manual and (not latest_auto or latest_target_manual[0] > latest_auto[0]):
        return "manual", latest_target_manual[1]
    if latest_auto and (not latest_target_manual or latest_auto[0] > latest_target_manual[0]):
        return "auto", latest_auto[1]
    if latest_other_manual:
        return "wrong_model", latest_other_manual[1]
    return "unknown", "no model mode telemetry found"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=300)
    parser.add_argument("--max-attempts", type=int, default=0, help="0 means unlimited")
    args = parser.parse_args()

    attempt = 0
    while True:
        attempt += 1
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{stamp}] readonly check {attempt}: {MODEL_NAME}", flush=True)

        container = run(
            [
                "docker",
                "inspect",
                "-f",
                "{{.State.Running}} {{.State.Status}} {{.Config.Image}}",
                "python-payment-container",
            ],
            timeout=20,
        )
        print(f"docker={container.stdout.strip() or 'unknown'}", flush=True)

        status = docker_repo_status()
        if status:
            print("repo_dirty=true", flush=True)
            print(status, flush=True)
        else:
            print("repo_dirty=false", flush=True)

        runtime_state, runtime_reason = runtime_model_state()
        print(f"runtime_state={runtime_state}: {runtime_reason}", flush=True)
        print("action=none; readonly monitor does not send probes, switch models, or run rollouts", flush=True)

        if args.max_attempts and attempt >= args.max_attempts:
            return 0
        print(f"sleeping {args.interval}s before next readonly check", flush=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
