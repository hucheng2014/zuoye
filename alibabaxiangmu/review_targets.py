import argparse
import json
import re
from pathlib import Path

from google import genai
from google.genai import types


import os

API_KEY = os.environ["GEMINI_API_KEY"]
client = genai.Client(vertexai=True, api_key=API_KEY)
BASE_DIR = Path("/home/jianglei/zuoye/alibabaxiangmu")
SCRATCH = BASE_DIR / "scratch"


def extract_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        return json.loads(cleaned[start : end + 1])
    return json.loads(cleaned)


def review_item(result: dict) -> dict:
    idx = result["index"] + 1
    video_data = Path(result["videoPath"]).read_bytes()
    prompt = f"""
你是提交前独立复核员，只检查候选 caption 是否可提交，不要重写完整答案。

按最新规则特别检查：
1. 语言选择是否正确。
2. 原始 caption 提到的主要声音候选是否遗漏。
3. 时间戳是否明显偏移、超出视频时长，或把长段持续背景声误当具体音效。
4. 持续背景声应在 2.1；2.2 只放具体、可定位的非人声音事件。
5. BGM 有则 8 项完整；无人声时 1.1/1.2/1.3 均为无。

只输出 JSON：
{{"passed": true, "blocking_issues": [], "warnings": [], "minimal_fixes": []}}

【题号】{idx}
【视频时长】{result["duration"]:.3f}s
【语言选择】{result["choice"]}

【原始 caption】
{result["originalCaption"]}

【候选 caption】
{result["caption"]}
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[types.Part.from_bytes(data=video_data, mime_type="video/mp4"), prompt],
    )
    raw = response.text or ""
    parsed = extract_json(raw)
    return {"index": idx, "raw": raw, "parsed": parsed}


def parse_items(value: str) -> set[int]:
    items: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            items.update(range(int(start), int(end) + 1))
        else:
            items.add(int(part))
    return items


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--items",
        help="comma-separated 1-based item numbers to review, e.g. 1 or 2,4,7-8; default reviews all results",
    )
    args = parser.parse_args()

    results = json.loads((SCRATCH / "batch_current_results.json").read_text(encoding="utf-8"))
    target_indices = parse_items(args.items) if args.items else {result["index"] + 1 for result in results}
    reviews = []
    for result in results:
        if result["index"] + 1 not in target_indices:
            continue
        print(f"[TargetReview] item {result['index'] + 1}", flush=True)
        review = review_item(result)
        reviews.append(review)
        print(json.dumps(review["parsed"], ensure_ascii=False, indent=2), flush=True)
    out = SCRATCH / "target_reviews.json"
    out.write_text(json.dumps(reviews, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
