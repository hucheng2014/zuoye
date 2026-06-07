import argparse
import asyncio
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from playwright.async_api import Locator, Page, async_playwright

from preflight_checks import preflight_caption, print_preflight_report
from solve_single_task import format_caption


import os

API_KEY = os.environ["GEMINI_API_KEY"]
client = genai.Client(vertexai=True, api_key=API_KEY)

BASE_DIR = Path("/home/jianglei/zuoye/alibabaxiangmu")
SCRATCH = BASE_DIR / "scratch"
CDP = "http://127.0.0.1:9237"


MAIN_PROMPT = """
请分析上传的视频，并结合给出的“原始 Caption”和最新标注规则，输出最终可提交的规范化音频 caption。

【最新硬性规则】
1. 第一行必须写：语言种类：中文/英文/小语种/无人声。
   - 有人声时按实际人声主语种选择；优先中英，中文或英文夹少量其他语言时按主语种选中文或英文。
   - 只有纯非中英文人声才选“小语种”。
   - 遇到小语种且具体词句无法听清时，1.3 里可直接写“`小语种`”；混合对话里，能听清的中文/英文部分正常逐句转写，小语种片段可单独保留“`小语种`”。
   - 完全无人说话、无人演唱、无人类发声时选“无人声”。
   - 副语言内容用 <> 标出。
2. 不要输出 markdown 代码块，不要保留 `<顺序分析结果>`、`<总结精炼结果>`、教程说明、占位符或分析废稿。
3. 必须使用完整结构：
总体概述:
详细描述:
1. 人声:
    1.1 通用录音环境与质量:
    1.2 说话/演唱人档案:
    1.3 说话/歌词内容:
2. 环境音与音效:
 2.1 环境背景声:
 2.2 音效:
3. 背景音乐:
4. 特殊合成音效:
4. 如果无人声，也必须写 1.1/1.2/1.3，三项都写“无”，不要省略子项。
5. 每句人声、每条具体音效都必须有时间戳，格式 `[MM:SS.mmm-MM:SS.mmm]`（分:秒.毫秒，不带小时位）。
6. 原 caption 把多句话合成一句时，按视频真实发声切开。时间戳要按实际声音节点，不要只复制原始粗略时间，且任何时间戳都不能超过视频实际时长。
7. 只为实际发声的说话人/演唱者建档；画面中出现但未发声的人不建档。大合唱难区分声部时可作为一个合唱演唱者整体描述。
8. 人的说话、演唱、喘息、喊叫、笑声、咳嗽声写在人声 1.3；掌声、欢呼声、狗叫、车辆、机械、脚步、物体碰撞等非人声音写在 2.2 音效。
9. 2.1 只用一句话描述录音环境背景声；若背景声被 BGM 掩盖，写“背景声被 BGM 覆盖”。持续性的室内底噪、低频嗡鸣、路噪、发动机底噪、机械持续运转声等，如果是贯穿背景而非离散事件，优先写在 2.1，不要强行放进 2.2。
10. 2.2 只列具体、可定位的非人声音事件或明显音效；每个具体音效描述以中文句号“。”结尾。欢呼声和掌声不能合并，必须拆成独立行。
11. 背景音乐若有，必须写满 8 项：音量、乐器、节奏与速度、录音质量与制作手法、旋律与和声、风格流派、氛围情绪、作用；无则写 `3. 背景音乐: 无`。
12. 背景音乐全程同一首时不要加时间戳；若背景音乐明显变化，则分段写时间戳，时间戳格式同人声/音效。
13. 带【】的可选字段只有在本段相比人物档案或通用环境出现明显变化时才写；无明显变化不要写。
14. 1.3 中每一条时间戳人声/歌词内容后面必须紧跟一行 `情感: ...`。不要把情感写到 1.2 人物档案中代替逐句情感。
15. 输出只给最终答案，不要解释。
"""


REVIEW_PROMPT = """
你是独立复核员。请重新观看/聆听上传的视频，对候选 caption 做内容复核。

重要限制：
1. 不要重写 caption，不要给可复制答案模板。
2. 不要用规则清单替代视频判断；以视频真实听感和画面为准。
3. 只输出 JSON，不要输出 markdown 或额外解释。

复核重点：
1. 语言种类是否符合：主语种优先中英，纯非中英文才小语种，完全无人声才无人声；对于无法听清的混合小语种片段，1.3 里写“`小语种`”属于允许写法，别误判为漏转写。
2. 未发声人物是否被误建档；实际发声者是否遗漏；合唱是否可作为整体。
3. 人声/非人声音效/BGM 分类是否正确，掌声和欢呼声是否分开。
4. 时间戳是否使用 `[MM:SS.mmm-MM:SS.mmm]`（分:秒.毫秒，不带小时位），顺序和起止点是否明显不符合视频。
5. 2.1/2.2 是否拆分清楚，音效是否逐条列出。
   - 持续背景底噪/嗡鸣/路噪/持续发动机或机械运转声应优先在 2.1 描述，除非视频中有具体可定位的声音事件。
6. BGM 有则 8 项完整，无则不虚构；全程同一首不应加时间戳，变化时才分段。
7. 是否有原始 caption 废稿、占位符或未修正错误残留。

JSON 格式：
{
  "passed": true,
  "observed_language": "中文",
  "blocking_issues": [],
  "warnings": []
}

observed_language 只能是 "中文"、"英文"、"小语种"、"无人声"。
blocking_issues 写不能提交的内容错误；没有则空数组。
warnings 写非阻断疑点；没有则空数组。
"""


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
    raise ValueError("review response does not contain JSON")


def detect_choice(raw: str, caption: str, original: str) -> str:
    match = re.search(r"语言种类[:：]\s*(中文|英文|小语种|无人声)", raw)
    if match:
        return match.group(1)

    if re.search(r"1\.1\s*通用录音环境与质量\s*[:：]\s*无", caption):
        return "无人声"

    combined = f"{raw}\n{caption}\n{original}"
    if re.search(r"(中文|普通话|粤语|汉语)", combined):
        return "中文"
    if re.search(r"(英文|英语|美式英语|英式英语|English)", combined, re.I):
        return "英文"
    if re.search(r"(韩语|尼泊尔语|日语|俄语|法语|意大利语|西班牙语|德语|泰语|阿拉伯语|葡萄牙语|土耳其语|印地语)", combined):
        return "小语种"
    return "中文"


async def select_page() -> Page:
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp(CDP)
    for context in browser.contexts:
        for page in context.pages:
            if "labelx.alibaba-inc.com/corpora/labeling/sdk" in page.url:
                await page.bring_to_front()
                page._batch_browser = browser  # type: ignore[attr-defined]
                page._batch_playwright = playwright  # type: ignore[attr-defined]
                return page
    await browser.close()
    await playwright.stop()
    raise RuntimeError("LabelX SDK page not found")


async def close_page_resources(page: Page) -> None:
    browser = getattr(page, "_batch_browser", None)
    playwright = getattr(page, "_batch_playwright", None)
    if browser:
        await browser.close()
    if playwright:
        await playwright.stop()


async def extract_items(page: Page) -> list[dict[str, Any]]:
    items = page.locator(".labelRender-item")
    count = await items.count()
    extracted: list[dict[str, Any]] = []
    for idx in range(count):
        item = items.nth(idx)
        textarea = item.locator("textarea").first
        video = item.locator("video").first
        if await textarea.count() == 0 or await video.count() == 0:
            continue
        blocks = await item.locator("div[class*='captionBlock']").all_inner_texts()
        original = "\n".join(
            t.strip()
            for t in blocks
            if t.strip() and t.strip() not in ("```", "```text")
        )
        video_src = await video.evaluate("el => el.currentSrc || el.src")
        duration = await video.evaluate("el => Number.isFinite(el.duration) ? el.duration : 0")
        checked = await item.evaluate("el => el.querySelector('input[type=radio]:checked')?.value || ''")
        current_text = await textarea.input_value()
        extracted.append(
            {
                "index": idx,
                "originalCaption": original,
                "videoSrc": video_src,
                "duration": float(duration or 0),
                "checked": checked,
                "currentTextLength": len(current_text),
            }
        )
    return extracted


async def download_video(page: Page, url: str, out: Path) -> bytes:
    if out.exists() and out.stat().st_size > 0:
        print(f"[Download] Reusing {out.name} ({out.stat().st_size} bytes).", flush=True)
        return out.read_bytes()

    last_error: Exception | None = None
    for attempt in range(1, 5):
        try:
            print(f"[Download] Fetching {out.name} attempt {attempt}/4...", flush=True)
            response = await page.context.request.get(url, timeout=300000)
            if not response.ok:
                raise RuntimeError(f"HTTP {response.status}")
            data = await response.body()
            if not data:
                raise RuntimeError("empty video body")
            out.write_bytes(data)
            return data
        except Exception as exc:
            last_error = exc
            print(f"[Download] {out.name} attempt {attempt}/4 failed: {exc}", flush=True)
            if attempt < 4:
                await page.wait_for_timeout(2000 * attempt)
    raise RuntimeError(f"video download failed after retries: {last_error}") from last_error


def save_results_checkpoint(results: list[dict[str, Any]]) -> None:
    tmp = SCRATCH / "batch_current_results.json.tmp"
    tmp.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(SCRATCH / "batch_current_results.json")


def generate_caption(
    video_data: bytes,
    original: str,
    duration: float,
    previous_caption: str = "",
    issues: list[str] | None = None,
) -> tuple[str, str, str]:
    correction = ""
    if previous_caption and issues:
        correction = (
            "\n\n【上一次候选 Caption】\n"
            f"{previous_caption}\n\n"
            "【必须修正的问题】\n"
            + "\n".join(f"- {issue}" for issue in issues)
            + "\n请重新观看/聆听视频后修正这些问题，输出完整最终答案，不要只输出差异。"
        )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=video_data, mime_type="video/mp4"),
            f"{MAIN_PROMPT}\n\n【视频实际时长】{duration:.3f} 秒。所有时间戳必须在 00:00:00.000 到该时长范围内。\n\n【原始 Caption】\n{original}\n{correction}",
        ],
    )
    raw = response.text or ""
    caption = format_caption(raw)
    choice = detect_choice(raw, caption, original)
    return raw, caption, choice


def review_caption(
    video_data: bytes,
    original: str,
    caption: str,
    choice: str,
    duration: float,
) -> tuple[dict[str, Any], list[str], str]:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=video_data, mime_type="video/mp4"),
            (
                f"{REVIEW_PROMPT}\n\n"
                f"【视频时长】{duration:.3f} 秒\n"
                f"【当前选择的语言种类】{choice}\n\n"
                f"【原始 Caption】\n{original}\n\n"
                f"【候选 Caption】\n{caption}\n"
            ),
        ],
    )
    raw = response.text or ""
    result = extract_json_object(raw)
    if not isinstance(result.get("blocking_issues"), list):
        result["blocking_issues"] = ["review JSON field blocking_issues is not a list"]
    if not isinstance(result.get("warnings"), list):
        result["warnings"] = ["review JSON field warnings is not a list"]

    language_errors: list[str] = []
    observed = result.get("observed_language")
    if observed not in ("中文", "英文", "小语种", "无人声"):
        language_errors.append(f"invalid observed_language: {observed!r}")
    elif observed != choice:
        language_errors.append(f"language mismatch: candidate={choice}, reviewer={observed}")
    return result, language_errors, raw


async def solve_all(page: Page, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    save_results_checkpoint(results)
    for item in items:
        idx = item["index"]
        video_hash = hashlib.sha1(item["videoSrc"].encode("utf-8")).hexdigest()[:10]
        video_path = SCRATCH / f"batch_item_{idx + 1:02d}_{video_hash}.mp4"
        video_data = await download_video(page, item["videoSrc"], video_path)

        raw = ""
        caption = ""
        choice = ""
        review: dict[str, Any] = {}
        language_errors: list[str] = []
        hard_errors: list[str] = []
        blocking: list[str] = []
        previous_caption = ""
        retry_issues: list[str] = []
        for attempt in range(1, 4):
            print(f"[Main] Generating item {idx + 1}/{len(items)} attempt {attempt}/3...", flush=True)
            raw, caption, choice = generate_caption(
                video_data,
                item["originalCaption"],
                duration=item["duration"],
                previous_caption=previous_caption,
                issues=retry_issues,
            )
            suffix = "" if attempt == 1 else f"_attempt{attempt}"
            (SCRATCH / f"batch_item_{idx + 1:02d}_gemini_raw{suffix}.txt").write_text(raw, encoding="utf-8")
            (SCRATCH / f"batch_item_{idx + 1:02d}_caption{suffix}.txt").write_text(caption, encoding="utf-8")
            if attempt == 1:
                (SCRATCH / f"batch_item_{idx + 1:02d}_gemini_raw.txt").write_text(raw, encoding="utf-8")
                (SCRATCH / f"batch_item_{idx + 1:02d}_caption.txt").write_text(caption, encoding="utf-8")

            print(f"[Review] Reviewing item {idx + 1}/{len(items)} choice={choice}...", flush=True)
            review, language_errors, review_raw = review_caption(
                video_data=video_data,
                original=item["originalCaption"],
                caption=caption,
                choice=choice,
                duration=item["duration"],
            )
            (SCRATCH / f"batch_item_{idx + 1:02d}_review_raw{suffix}.txt").write_text(review_raw, encoding="utf-8")
            if attempt == 1:
                (SCRATCH / f"batch_item_{idx + 1:02d}_review_raw.txt").write_text(review_raw, encoding="utf-8")

            hard_errors = preflight_caption(caption, video_duration=item["duration"] or None)
            blocking = list(language_errors)
            blocking.extend(str(x) for x in (review.get("blocking_issues") or []))
            if not review.get("passed"):
                blocking.append("review returned passed=false")
            blocking.extend(hard_errors)
            if not blocking:
                break
            previous_caption = caption
            retry_issues = blocking
            print(f"[Retry] Item {idx + 1} attempt {attempt} failed; will retry if attempts remain.", flush=True)

        result = {
            **item,
            "choice": choice,
            "caption": caption,
            "review": review,
            "languageErrors": language_errors,
            "hardErrors": hard_errors,
            "blocking": blocking,
            "videoPath": str(video_path),
        }
        results.append(result)
        save_results_checkpoint(results)
        if blocking:
            print(f"[Blocked] Item {idx + 1} failed:", flush=True)
            for error in blocking:
                print(f"  - {error}", flush=True)
            break
        (SCRATCH / f"batch_item_{idx + 1:02d}_caption_final.txt").write_text(caption, encoding="utf-8")
        (SCRATCH / f"batch_item_{idx + 1:02d}_review_final.json").write_text(
            json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[OK] Item {idx + 1} passed generation, review, and hard checks.", flush=True)
    save_results_checkpoint(results)
    return results


async def choose_language(item: Locator, choice: str) -> None:
    radio = item.locator(f"input[type='radio'][value='{choice}']").first
    await radio.check(force=True)
    await item.page.wait_for_timeout(300)
    checked = await item.evaluate("el => el.querySelector('input[type=radio]:checked')?.value || ''")
    if checked != choice:
        raise RuntimeError(f"language radio mismatch after check: expected={choice}, checked={checked!r}")


async def fill_all(page: Page, results: list[dict[str, Any]]) -> None:
    items = page.locator(".labelRender-item")
    if await items.count() != len(results):
        raise RuntimeError(f"page item count mismatch before fill: page={await items.count()}, results={len(results)}")
    for result in results:
        idx = result["index"]
        item = items.nth(idx)
        print(f"[Fill] Filling item {idx + 1}/{len(results)}...", flush=True)
        textarea = item.locator("textarea").first
        await textarea.fill(result["caption"])
        await textarea.blur()
        await choose_language(item, result["choice"])
        filled = await textarea.input_value()
        checked = await item.evaluate("el => el.querySelector('input[type=radio]:checked')?.value || ''")
        errors = preflight_caption(filled, video_duration=result["duration"] or None)
        if filled.strip() != result["caption"].strip():
            errors.append("textarea content mismatch after fill")
        if checked != result["choice"]:
            errors.append(f"language mismatch after fill: expected={result['choice']}, checked={checked!r}")
        if errors:
            print_preflight_report(errors)
            raise RuntimeError(f"item {idx + 1} failed post-fill verification")
        await wait_for_save(page)
    await verify_page_values(page, results, label="after fill")
    await wait_for_save(page)
    await page.screenshot(path=str(SCRATCH / "batch_current_filled.png"), full_page=True)


async def wait_for_save(page: Page) -> None:
    for _ in range(40):
        body = await page.locator("body").inner_text()
        messages = await page.evaluate(
            """() => Array.from(document.querySelectorAll('.ant-v5-message, .ant-message'))
              .map(e => e.innerText.trim()).filter(Boolean)"""
        )
        if "保存成功" in body or any("保存成功" in message for message in messages):
            return
        await page.wait_for_timeout(500)
    raise RuntimeError("save success was not observed")


async def verify_page_values(page: Page, results: list[dict[str, Any]], label: str) -> None:
    items = page.locator(".labelRender-item")
    errors: list[str] = []
    count = await items.count()
    if count != len(results):
        errors.append(f"{label}: page item count mismatch: page={count}, expected={len(results)}")
    for result in results:
        idx = result["index"]
        if idx >= count:
            errors.append(f"{label}: item {idx + 1} missing on page")
            continue
        item = items.nth(idx)
        text = await item.locator("textarea").first.input_value()
        checked = await item.evaluate("el => el.querySelector('input[type=radio]:checked')?.value || ''")
        if text.strip() != result["caption"].strip():
            errors.append(f"{label}: item {idx + 1} textarea does not match expected caption")
        if checked != result["choice"]:
            errors.append(f"{label}: item {idx + 1} language mismatch: expected={result['choice']}, checked={checked!r}")
        errors.extend(
            f"{label}: item {idx + 1}: {e}"
            for e in preflight_caption(text, video_duration=result["duration"] or None)
        )
    if errors:
        await page.screenshot(path=str(SCRATCH / f"batch_current_verify_failed_{label.replace(' ', '_')}.png"), full_page=True)
        raise RuntimeError("\n".join(errors))


async def verify_after_reload(page: Page, results: list[dict[str, Any]]) -> None:
    print("[Verify] Waiting 5 seconds for all auto-saves to commit...", flush=True)
    await page.wait_for_timeout(5000)
    print("[Verify] Reloading page to confirm saved values persist...", flush=True)
    await page.reload(wait_until="domcontentloaded")
    await page.wait_for_selector(".labelRender-item textarea", timeout=30000)
    await page.wait_for_timeout(3000)
    await verify_page_values(page, results, label="after reload")
    await page.screenshot(path=str(SCRATCH / "batch_current_after_reload_verified.png"), full_page=True)


def load_verified_results(expected_count: int | None = None) -> list[dict[str, Any]]:
    path = SCRATCH / "batch_current_results.json"
    if not path.exists():
        raise RuntimeError("scratch/batch_current_results.json does not exist")
    results = json.loads(path.read_text(encoding="utf-8"))
    if expected_count is not None and len(results) != expected_count:
        raise RuntimeError(f"expected {expected_count} generated results, found {len(results)}")
    if not results:
        raise RuntimeError("generated results are empty")
    blocking = {
        int(result.get("index", -1)) + 1: result.get("blocking")
        for result in results
        if result.get("blocking")
    }
    if blocking:
        raise RuntimeError(f"generated results still contain blocking issues: {blocking}")
    for idx, result in enumerate(results, start=1):
        for key in ("caption", "choice", "duration", "index"):
            if key not in result:
                raise RuntimeError(f"result item {idx} missing {key}")
    return results


def verify_results_match_items(results: list[dict[str, Any]], items: list[dict[str, Any]]) -> None:
    if len(results) != len(items):
        raise RuntimeError(f"result/page item count mismatch: results={len(results)}, page={len(items)}")
    errors: list[str] = []
    for result, item in zip(results, items):
        idx = int(result.get("index", -1))
        if idx != int(item.get("index", -2)):
            errors.append(f"item {item.get('index', '?') + 1}: index mismatch result={idx}")
        result_duration = float(result.get("duration") or 0)
        item_duration = float(item.get("duration") or 0)
        if abs(result_duration - item_duration) > 0.05:
            errors.append(
                f"item {idx + 1}: duration mismatch result={result_duration:.3f}, page={item_duration:.3f}"
            )
        result_original = (result.get("originalCaption") or "").strip()
        item_original = (item.get("originalCaption") or "").strip()
        if result_original != item_original:
            errors.append(f"item {idx + 1}: original caption mismatch")
    if errors:
        raise RuntimeError("current page does not match generated results:\n" + "\n".join(errors))


async def submit_page(page: Page) -> dict[str, Any]:
    items = page.locator(".labelRender-item")
    item_count = await items.count()
    page_errors: list[str] = []
    if item_count <= 0:
        page_errors.append("no items found before submit")
    for idx in range(item_count):
        item = items.nth(idx)
        textarea = item.locator("textarea").first
        text = await textarea.input_value()
        checked = await item.evaluate("el => el.querySelector('input[type=radio]:checked')?.value || ''")
        duration = await item.locator("video").first.evaluate("el => Number.isFinite(el.duration) ? el.duration : 0")
        if not checked:
            page_errors.append(f"item {idx + 1}: language not selected")
        page_errors.extend(f"item {idx + 1}: {e}" for e in preflight_caption(text, video_duration=float(duration or 0) or None))
    if page_errors:
        await page.screenshot(path=str(SCRATCH / "batch_current_submit_blocked.png"), full_page=True)
        return {
            "submitted": False,
            "messages": [],
            "url": page.url,
            "bodyStart": "",
            "blocking": page_errors,
        }

    before_url = page.url
    print(f"[Submit] Clicking 提交任务 after all {item_count} items passed.", flush=True)
    await page.locator('button:has-text("提交任务")').first.click(force=True)
    seen: list[str] = []
    body = ""
    success = False
    for _ in range(60):
        await page.wait_for_timeout(500)
        body = await page.locator("body").inner_text()
        messages = await page.evaluate(
            """() => Array.from(document.querySelectorAll('.ant-v5-message, .ant-message'))
              .map(e => e.innerText.trim()).filter(Boolean)"""
        )
        for message in messages:
            if message not in seen:
                seen.append(message)
        if any(word in body for word in ("提交成功", "任务提交成功", "暂无任务")):
            success = True
            break
        if page.url != before_url:
            success = True
            break
    await page.screenshot(path=str(SCRATCH / "batch_current_after_submit.png"), full_page=True)
    return {"submitted": success, "messages": seen, "url": page.url, "bodyStart": body[:1000]}


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fill", action="store_true", help="fill the page after all checks pass")
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--use-results", action="store_true", help="use scratch/batch_current_results.json instead of regenerating")
    args = parser.parse_args()

    page = await select_page()
    try:
        items = await extract_items(page)
        if not items:
            raise RuntimeError("no rendered tasks found on current page")
        (SCRATCH / "batch_current_extract.json").write_text(
            json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[Extract] Found {len(items)} rendered tasks on current page.", flush=True)

        if args.use_results:
            results = load_verified_results(expected_count=len(items))
            verify_results_match_items(results, items)
            print(f"[Load] Loaded {len(results)} previously verified generated results.", flush=True)
        else:
            results = await solve_all(page, items)
        if len(results) != len(items) or any(r["blocking"] for r in results):
            print("[Stop] Not filling/submitting because at least one item failed.", flush=True)
            return

        if not args.fill and not args.submit:
            print(f"[Safe Stop] Generated and verified all {len(results)} items. Page was not filled.", flush=True)
            return

        await fill_all(page, results)
        print(f"[Fill] All {len(results)} items filled and in-page verified.", flush=True)
        await verify_after_reload(page, results)
        print("[Verify] Reload verification passed; saved values persisted.", flush=True)
        if not args.submit:
            print("[Safe Stop] Page not submitted. Re-run with --submit to submit.", flush=True)
            return

        submit_result = await submit_page(page)
        (SCRATCH / "batch_current_submit_result.json").write_text(
            json.dumps(submit_result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(submit_result, ensure_ascii=False, indent=2), flush=True)
        if not submit_result["submitted"]:
            raise RuntimeError("submit was not confirmed")
    finally:
        await close_page_resources(page)


if __name__ == "__main__":
    asyncio.run(main())
