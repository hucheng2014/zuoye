import json
import time
from pathlib import Path

import requests
from huggingface_hub import HfApi, hf_hub_url


REPO_ID = "Systran/faster-whisper-large-v3"
TARGET_DIR = Path(r"C:\Users\BERN7P\codex-browser\models\faster-whisper-large-v3")
STATUS_PATH = Path(r"C:\Users\BERN7P\codex-browser\download_faster_whisper_large_v3.status.json")


def write_status(payload: dict) -> None:
    STATUS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    api = HfApi()
    info = api.model_info(REPO_ID, files_metadata=True, timeout=60)
    files = []
    total_bytes = 0
    for sibling in info.siblings:
        size = int(getattr(sibling, "size", 0) or 0)
        files.append({"path": sibling.rfilename, "size": size})
        total_bytes += size
    files.sort(key=lambda item: item["size"], reverse=True)

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "codex-downloader/1.0"

    downloaded_total = 0
    started_at = time.time()
    last_tick = started_at
    last_tick_bytes = 0

    write_status(
        {
            "status": "starting",
            "repo_id": REPO_ID,
            "target_dir": str(TARGET_DIR),
            "total_bytes": total_bytes,
            "downloaded_bytes": 0,
            "percent": 0.0,
            "speed_bytes_per_sec": 0.0,
            "eta_seconds": None,
            "current_file": None,
            "started_at": started_at,
            "files": files,
        }
    )

    for item in files:
        rel_path = item["path"]
        size = item["size"]
        dest = TARGET_DIR / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)

        url = hf_hub_url(REPO_ID, filename=rel_path)
        with session.get(url, stream=True, timeout=(30, 300), allow_redirects=True) as response:
            response.raise_for_status()
            temp_path = dest.with_suffix(dest.suffix + ".part")
            file_downloaded = 0
            with temp_path.open("wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    f.write(chunk)
                    file_downloaded += len(chunk)
                    downloaded_total += len(chunk)
                    now = time.time()
                    if now - last_tick >= 1:
                        interval = now - last_tick
                        delta = downloaded_total - last_tick_bytes
                        speed = delta / interval if interval > 0 else 0.0
                        remaining = max(total_bytes - downloaded_total, 0)
                        eta = remaining / speed if speed > 0 else None
                        write_status(
                            {
                                "status": "downloading",
                                "repo_id": REPO_ID,
                                "target_dir": str(TARGET_DIR),
                                "total_bytes": total_bytes,
                                "downloaded_bytes": downloaded_total,
                                "percent": round(downloaded_total * 100 / total_bytes, 3) if total_bytes else 0.0,
                                "speed_bytes_per_sec": speed,
                                "eta_seconds": eta,
                                "current_file": rel_path,
                                "current_file_size": size,
                                "current_file_downloaded": file_downloaded,
                                "started_at": started_at,
                                "elapsed_seconds": now - started_at,
                            }
                        )
                        last_tick = now
                        last_tick_bytes = downloaded_total
            temp_path.replace(dest)

        now = time.time()
        elapsed = now - started_at
        avg_speed = downloaded_total / elapsed if elapsed > 0 else 0.0
        remaining = max(total_bytes - downloaded_total, 0)
        eta = remaining / avg_speed if avg_speed > 0 else None
        write_status(
            {
                "status": "downloading",
                "repo_id": REPO_ID,
                "target_dir": str(TARGET_DIR),
                "total_bytes": total_bytes,
                "downloaded_bytes": downloaded_total,
                "percent": round(downloaded_total * 100 / total_bytes, 3) if total_bytes else 0.0,
                "speed_bytes_per_sec": avg_speed,
                "eta_seconds": eta,
                "current_file": rel_path,
                "current_file_size": size,
                "current_file_downloaded": size,
                "started_at": started_at,
                "elapsed_seconds": elapsed,
            }
        )

    finished_at = time.time()
    write_status(
        {
            "status": "completed",
            "repo_id": REPO_ID,
            "target_dir": str(TARGET_DIR),
            "total_bytes": total_bytes,
            "downloaded_bytes": downloaded_total,
            "percent": 100.0,
            "speed_bytes_per_sec": downloaded_total / (finished_at - started_at) if finished_at > started_at else 0.0,
            "eta_seconds": 0,
            "current_file": None,
            "started_at": started_at,
            "elapsed_seconds": finished_at - started_at,
            "finished_at": finished_at,
        }
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        write_status(
            {
                "status": "failed",
                "error": repr(exc),
                "failed_at": time.time(),
            }
        )
        raise
