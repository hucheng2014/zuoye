#!/usr/bin/env python3
"""Validate AD Search Ads batch records.

This tool is intentionally offline-only:
- it does not connect to the browser;
- it does not choose ratings;
- it does not fill or submit tasks.

Use it to enforce the SOP before submitting a batch.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ALLOWED_RATINGS = {"Excellent", "Good", "Acceptable", "Bad"}
VERIFY_FLAGS = [
    "all_radios_selected",
    "all_comments_present",
    "comments_match_each_task",
    "bad_comments_explain_why",
    "no_required_errors",
    "record_matches_page",
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").lower())


def init_file(path: Path, count: int) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    data: dict[str, Any] = {
        "batch_id": path.stem,
        "project": "AD Search Ads Relevance",
        "operator": "",
        "created_at": now,
        "source_page": "tryrating current page",
        "tasks": [],
        "pre_submit_verification": {flag: False for flag in VERIFY_FLAGS},
        "submit": {
            "authorized_by_user": False,
            "submitted": False,
            "submitted_at": "",
            "post_submit_status": "",
        },
    }
    for i in range(1, count + 1):
        data["tasks"].append(
            {
                "index": i,
                "task_id": "",
                "query": "",
                "query_intent": "",
                "ad": {"name": "", "subtitle": "", "developer": "", "type": "app"},
                "evidence": [{"source": "", "note": ""}],
                "relationship_analysis": "",
                "why_not_higher": "",
                "why_not_lower": "",
                "rating": "",
                "comment": "",
                "pre_submit_checked": False,
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Initialized {path} with {count} tasks")


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"ERROR: cannot read JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("ERROR: batch file must be a JSON object")
    return data


def has_meaningful_evidence(task: dict[str, Any]) -> bool:
    evidence = task.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return False
    for item in evidence:
        if isinstance(item, dict) and (item.get("note") or item.get("source")):
            return True
        if isinstance(item, str) and item.strip():
            return True
    return False


def comment_mentions_task(comment: str, query: str, app_name: str) -> bool:
    c = normalize(comment)
    q = normalize(query)
    a = normalize(app_name)
    # Short Chinese/brand queries may be enough if exact; app names can be long, use first 4 chars too.
    query_ok = bool(q and q in c)
    app_ok = bool(a and (a in c or (len(a) >= 4 and a[:4] in c)))
    return query_ok and app_ok


def validate(path: Path, require_checked: bool) -> int:
    data = load_json(path)
    errors: list[str] = []
    warnings: list[str] = []

    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("batch.tasks must be a non-empty list")
        tasks = []

    seen_comments: dict[str, int] = {}

    for pos, task in enumerate(tasks, start=1):
        label = f"task[{pos}]"
        if not isinstance(task, dict):
            errors.append(f"{label}: must be an object")
            continue

        index = task.get("index", pos)
        prefix = f"task #{index}"
        query = str(task.get("query") or "").strip()
        ad = task.get("ad") if isinstance(task.get("ad"), dict) else {}
        app_name = str(ad.get("name") or "").strip()
        rating = str(task.get("rating") or "").strip()
        comment = str(task.get("comment") or "").strip()

        if not query:
            errors.append(f"{prefix}: missing query")
        if not app_name:
            errors.append(f"{prefix}: missing ad.name")
        if not task.get("query_intent"):
            errors.append(f"{prefix}: missing query_intent")
        if not task.get("relationship_analysis"):
            errors.append(f"{prefix}: missing relationship_analysis")
        if rating not in ALLOWED_RATINGS:
            errors.append(f"{prefix}: rating must be one of {sorted(ALLOWED_RATINGS)}, got {rating!r}")
        if len(comment) < 40:
            errors.append(f"{prefix}: comment is too short or empty")
        if rating == "Bad" and len(comment) < 60:
            errors.append(f"{prefix}: Bad rating requires an explanatory comment")
        if query and app_name and comment and not comment_mentions_task(comment, query, app_name):
            warnings.append(f"{prefix}: comment may not mention both query and ad name; check for cross-task mix-up")
        if not has_meaningful_evidence(task):
            warnings.append(f"{prefix}: no evidence/source note recorded")
        if require_checked and task.get("pre_submit_checked") is not True:
            errors.append(f"{prefix}: pre_submit_checked must be true before submit")

        key = normalize(comment)
        if key:
            if key in seen_comments:
                warnings.append(f"{prefix}: comment duplicates task #{seen_comments[key]}; verify it is not copied blindly")
            else:
                seen_comments[key] = int(index) if isinstance(index, int) else pos

    verification = data.get("pre_submit_verification")
    if require_checked:
        if not isinstance(verification, dict):
            errors.append("pre_submit_verification must be an object")
        else:
            for flag in VERIFY_FLAGS:
                if verification.get(flag) is not True:
                    errors.append(f"pre_submit_verification.{flag} must be true before submit")

    for warning in warnings:
        print(f"WARN: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1

    print(f"OK: {len(tasks)} task(s) validated with {len(warnings)} warning(s)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an AD Search Ads batch record")
    parser.add_argument("path", nargs="?", help="batch JSON file")
    parser.add_argument("--init", metavar="PATH", help="create a blank batch JSON file")
    parser.add_argument("--count", type=int, default=5, help="number of tasks for --init (default: 5)")
    parser.add_argument("--require-checked", action="store_true", help="require task and pre-submit checkboxes to be true")
    args = parser.parse_args()

    if args.init:
        if args.count <= 0:
            raise SystemExit("ERROR: --count must be positive")
        init_file(Path(args.init), args.count)
        return 0

    if not args.path:
        parser.error("provide a batch JSON file or use --init")
    return validate(Path(args.path), args.require_checked)


if __name__ == "__main__":
    sys.exit(main())
