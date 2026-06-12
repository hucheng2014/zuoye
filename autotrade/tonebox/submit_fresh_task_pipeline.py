#!/usr/bin/env python3
"""Create, fill, and verify a fresh Bitable task group for the current run."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def run_step(label: str, args: list[str]) -> None:
    print(f"\n== {label} ==")
    subprocess.run(args, cwd=BASE_DIR, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fresh-task Bitable submission pipeline.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Create the new task group and upload attachments. Without this, only local review and a create plan run.",
    )
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Only run local review and create an offline new-group plan.",
    )
    args = parser.parse_args()

    run_step("local pre-submit review", ["bash", "batch_runner.sh", "review"])

    group_cmd = [sys.executable, "submit_new_task_group.py"]
    if args.apply and not args.plan_only:
        group_cmd.append("--apply")
    run_step("create fresh task group" if args.apply and not args.plan_only else "plan fresh task group", group_cmd)

    if args.plan_only:
        return 0

    if not args.apply:
        print("\nDry run complete. Re-run with --apply to create records and upload attachments.")
        return 0

    run_step("upload attachments to fresh task group", [sys.executable, "submit_new_task_attachments.py", "--apply"])
    run_step("build Docker image and upload build metadata", [sys.executable, "repair_docker_build_metadata.py", "--apply"])
    run_step("attachment/server verify", [sys.executable, "submit_new_task_attachments.py", "--verify-only"])
    run_step("post-submit table verify", [sys.executable, "verify_fresh_task_remote.py"])
    print("\nFresh task submission complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
