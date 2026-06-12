#!/usr/bin/env python3
"""Archive the completed trial workspace and stop completed trial containers."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ARCHIVE_DIR = BASE_DIR / "archive"

ROOT_FILES = [
    ".trial_resume.json",
    "Dockerfile",
    "docker_build_success.png",
    "repo.zip",
    "python-grade.zip",
    "rollout_data.json",
    "trial_log.csv",
]
ROOT_DIRS = [
    "repo",
    "new_task_backups",
    "restore_backups",
    "sample_inspection",
]
PATTERNS = [
    "prompt*.patch",
    "prompt_*_filled.png",
    "prompt_*_submitted.png",
    "rollout_p*_preview.png",
]


def collect_paths() -> list[Path]:
    paths: list[Path] = []
    for name in ROOT_FILES:
        path = BASE_DIR / name
        if path.exists():
            paths.append(path)
    for name in ROOT_DIRS:
        path = BASE_DIR / name
        if path.exists():
            paths.append(path)
    for pattern in PATTERNS:
        paths.extend(sorted(BASE_DIR.glob(pattern)))
    lock = BASE_DIR / ".batch_runner.lock"
    if lock.exists():
        paths.append(lock)
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if path not in seen:
            unique.append(path)
            seen.add(path)
    return unique


def move_path(src: Path, dst: Path, *, apply: bool) -> None:
    if not apply:
        print(f"DRY move {src.relative_to(BASE_DIR)} -> {dst.relative_to(BASE_DIR)}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))


def stop_trial_containers(*, apply: bool) -> list[str]:
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}\t{{.Image}}"],
        cwd=BASE_DIR,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        print(result.stderr.strip())
        return []
    names: list[str] = []
    for line in result.stdout.splitlines():
        name, _, image = line.partition("\t")
        is_trial_image = "-trial" in image
        is_python_task_container = name.startswith("python-") and name.endswith("-container")
        if is_trial_image or is_python_task_container:
            names.append(name)
    for name in names:
        if apply:
            subprocess.run(["docker", "stop", name], cwd=BASE_DIR, check=True)
            print(f"stopped_container={name}")
        else:
            print(f"DRY stop container {name}")
    return names


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive completed Trae trial artifacts.")
    parser.add_argument("--apply", action="store_true", help="Actually move files and stop trial containers.")
    parser.add_argument("--label", default="", help="Archive label. Defaults to completed-trial timestamp.")
    parser.add_argument("--keep-containers", action="store_true", help="Do not stop completed trial containers.")
    args = parser.parse_args()

    label = args.label or f"completed-trial-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    dest = ARCHIVE_DIR / label
    paths = collect_paths()
    print(f"archive_dir={dest}")
    print(f"items={len(paths)} apply={args.apply}")
    for path in paths:
        move_path(path, dest / path.name, apply=args.apply)

    stopped: list[str] = []
    if not args.keep_containers:
        stopped = stop_trial_containers(apply=args.apply)

    manifest = {
        "label": label,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "archived_items": [str(path.relative_to(BASE_DIR)) for path in paths],
        "stopped_containers": stopped,
    }
    if args.apply:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "archive_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("archive complete" if args.apply else "dry run complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
