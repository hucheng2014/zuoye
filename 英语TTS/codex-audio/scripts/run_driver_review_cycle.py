import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract a page through the browser driver, review it offline, and optionally apply edits.",
    )
    parser.add_argument("--driver-in", required=True, help="Path to driver RPC input JSON.")
    parser.add_argument("--driver-out", required=True, help="Path to driver RPC output JSON.")
    parser.add_argument(
        "--work-dir",
        required=True,
        help="Directory for snapshots, reviews, audio files, and edits.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply generated edits back to the controlled page.",
    )
    parser.add_argument(
        "--progress-file",
        help="Optional JSON file updated while review_page_audio.py is running.",
    )
    return parser.parse_args()


def write_json_no_bom(path: Path, payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def timestamp() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def wait_for_driver_result(
    driver_out: Path,
    request_id: str,
    action: str,
    timeout_seconds: float = 60.0,
) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if driver_out.exists():
            try:
                payload = load_json(driver_out)
            except json.JSONDecodeError:
                time.sleep(0.25)
                continue
            if payload.get("id") == request_id and payload.get("action") == action:
                return payload
        time.sleep(0.25)
    raise TimeoutError(f"Timed out waiting for driver action={action} id={request_id}")


def run_subprocess(args: list[str]) -> None:
    subprocess.run(args, check=True)


def main() -> None:
    args = parse_args()
    driver_in = Path(args.driver_in)
    driver_out = Path(args.driver_out)
    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    ts = timestamp()
    snapshot_path = work_dir / f"page_snapshot_{ts}.json"
    review_prefix = work_dir / f"review_{ts}"
    edits_path = work_dir / f"edits_{ts}.json"
    audio_dir = work_dir / f"audios_{ts}"

    request_id = ts
    write_json_no_bom(
        driver_in,
        {
            "id": request_id,
            "action": "extract",
            "outPath": str(snapshot_path),
        },
    )
    extract_result = wait_for_driver_result(driver_out, request_id=request_id, action="extract")

    run_subprocess(
        [
            sys.executable,
            str(Path(__file__).with_name("review_page_audio.py")),
            "--snapshot",
            str(snapshot_path),
            "--audio-dir",
            str(audio_dir),
            "--output-prefix",
            str(review_prefix),
            *(
                ["--progress-file", args.progress_file]
                if args.progress_file
                else []
            ),
        ]
    )

    run_subprocess(
        [
            sys.executable,
            str(Path(__file__).with_name("build_page_edits.py")),
            "--review",
            str(review_prefix.with_suffix(".json")),
            "--output",
            str(edits_path),
        ]
    )

    edits_payload = load_json(edits_path)
    applied_result: dict[str, Any] | None = None
    if args.apply and edits_payload.get("edits"):
        request_id = f"{ts}_apply"
        write_json_no_bom(
            driver_in,
            {
                "id": request_id,
                "action": "apply",
                "edits": edits_payload["edits"],
            },
        )
        applied_result = wait_for_driver_result(driver_out, request_id=request_id, action="apply")

    summary = {
        "snapshot": str(snapshot_path),
        "review_json": str(review_prefix.with_suffix(".json")),
        "review_md": str(review_prefix.with_suffix(".md")),
        "edits": str(edits_path),
        "edit_count": edits_payload.get("count", 0),
        "progress_file": args.progress_file,
        "applied": applied_result,
        "page_count": extract_result.get("data", {}).get("count"),
    }
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
