import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build safe page edits from a review JSON report.",
    )
    parser.add_argument("--review", required=True, help="Path to review JSON.")
    parser.add_argument("--output", required=True, help="Path to edits JSON.")
    parser.add_argument(
        "--noise-yes-threshold",
        type=float,
        default=0.35,
        help="Only auto-flip noise to yes when score is at or above this threshold.",
    )
    parser.add_argument(
        "--noise-no-threshold",
        type=float,
        default=0.05,
        help="Only auto-flip noise to no when score is at or below this threshold.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def noise_index_from_label(label: str) -> int:
    return 0 if label == "yes" else 1


def maybe_build_edit(
    item: dict[str, Any],
    noise_yes_threshold: float,
    noise_no_threshold: float,
) -> dict[str, Any] | None:
    selected_indexes = list(item.get("page_selected_indexes") or [])
    if not selected_indexes:
        return None

    edit: dict[str, Any] = {"filename": item["filename"], "selectedIndexes": selected_indexes.copy()}
    changed = False

    page_noise_selected = item.get("page_noise_selected")
    noise_score = float(item.get("noise_score", 0.0))
    noise_suggestion = item.get("noise_suggestion")

    if page_noise_selected is not None and len(edit["selectedIndexes"]) >= 5:
        if noise_suggestion == "yes" and noise_score >= noise_yes_threshold:
            wanted = noise_index_from_label("yes")
            if page_noise_selected != wanted:
                edit["selectedIndexes"][4] = wanted
                changed = True
        elif noise_suggestion == "no" and noise_score <= noise_no_threshold:
            wanted = noise_index_from_label("no")
            if page_noise_selected != wanted:
                edit["selectedIndexes"][4] = wanted
                changed = True

    if item.get("text_change_suggested"):
        wanted_text = item.get("transcript_consensus", {}).get("text", "").strip()
        if wanted_text and wanted_text != (item.get("page_text") or "").strip():
            edit["text"] = wanted_text
            changed = True

    return edit if changed else None


def main() -> None:
    args = parse_args()
    review = load_json(Path(args.review))
    edits = []
    for item in review.get("items", []):
        edit = maybe_build_edit(
            item,
            noise_yes_threshold=args.noise_yes_threshold,
            noise_no_threshold=args.noise_no_threshold,
        )
        if edit:
            edits.append(edit)

    payload = {
        "review": args.review,
        "count": len(edits),
        "edits": edits,
    }
    write_json(Path(args.output), payload)
    print(json.dumps({"output": args.output, "count": len(edits)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
