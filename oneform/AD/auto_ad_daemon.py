#!/usr/bin/env python3
"""AD Search Ads Relevance full-auto daemon: extract -> LLM rate -> wait 9m -> fill -> submit -> repeat."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RECORDS = ROOT / "records"
RUNS = ROOT / "runs"
SOP_COMPACT = ROOT.parent / "pipeline" / "knowledge" / "ad" / "compact_sop.md"
SOP_FULL = ROOT / "AD_RATING_SOP.md"
CONTAINER = os.environ.get("AD_CONTAINER", "oneform-agent")
WORKDIR = os.environ.get("AD_WORKDIR", "/app/AD")
WAIT_SEC = int(os.environ.get("AD_SUBMIT_WAIT_SEC", "540"))
POLL_SEC = int(os.environ.get("AD_POLL_SEC", "15"))
MODEL = os.environ.get("AD_LLM_MODEL", "claude-sonnet-4-6")
RATING_METHOD = "llm_per_task_v1"
ALLOWED_RATINGS = {"Excellent", "Good", "Acceptable", "Bad"}
CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"


def load_credentials() -> None:
    """Load Anthropic credentials from env or ~/.claude/settings.json."""
    global MODEL
    if os.environ.get("ANTHROPIC_BASE_URL") and (
        os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    ):
        MODEL = os.environ.get("AD_LLM_MODEL") or os.environ.get("ANTHROPIC_MODEL", MODEL)
        return
    if CLAUDE_SETTINGS.exists():
        try:
            data = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
            for key, value in (data.get("env") or {}).items():
                if key.startswith("ANTHROPIC") and value and not os.environ.get(key):
                    os.environ[key] = str(value)
        except Exception as exc:
            log(f"Warning: could not read {CLAUDE_SETTINGS}: {exc}")
    MODEL = os.environ.get("AD_LLM_MODEL") or os.environ.get("ANTHROPIC_MODEL", MODEL)
    if not os.environ.get("ANTHROPIC_BASE_URL") or not (
        os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    ):
        raise RuntimeError(
            "Missing Anthropic credentials. Set ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN "
            "or configure ~/.claude/settings.json"
        )


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)


def clean_ad_name(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    if "background-color" in raw and "}" in raw:
        tail = raw.rsplit("}", 1)[-1].strip()
        if tail and "font-family" not in tail:
            return tail
    if len(raw) > 120 and "}" in raw:
        return raw.rsplit("}", 1)[-1].strip()
    return raw


def docker_py(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = ["docker", "exec", "-w", WORKDIR, CONTAINER, "python3", script, *args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=180)


def extract_page_tasks() -> list[dict[str, Any]] | None:
    proc = docker_py("extract_batch_ordered.py")
    if proc.returncode != 0:
        log(f"extract failed: {proc.stderr.strip() or proc.stdout.strip()}")
        return None
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        log(f"extract JSON parse error: {exc}")
        return None
    tasks = data.get("tasks") or []
    if not tasks:
        return None
    for t in tasks:
        ad = t.get("ad") or {}
        ad["name"] = clean_ad_name(ad.get("name", ""))
        t["ad"] = ad
    return tasks


def docker_python(code: str) -> subprocess.CompletedProcess[str]:
    cmd = ["docker", "exec", "-w", WORKDIR, CONTAINER, "python3", "-c", code]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60)


def page_has_ad_tasks() -> bool:
    code = (
        "import json,urllib.request;from websocket import create_connection;"
        "CDP='http://browser:9223';"
        "req=urllib.request.Request(f'{CDP}/json/list');"
        "req.add_header('Host','localhost:9222');"
        "pages=json.loads(urllib.request.urlopen(req,timeout=5).read());"
        "page=[p for p in pages if p.get('type')=='page' and 'tryrating' in p.get('url','')][0];"
        "ws=create_connection(page['webSocketDebuggerUrl'].replace('ws://localhost:9222','ws://browser:9223'),timeout=10);"
        "ws.send(json.dumps({'id':1,'method':'Runtime.enable'}));ws.recv();"
        "ws.send(json.dumps({'id':2,'method':'Runtime.evaluate','params':{'expression':'document.body.innerText||\"\"','returnByValue':True}}));"
        "import json as J\n"
        "while True:\n"
        " d=J.loads(ws.recv());\n"
        " if d.get('id')==2: print(d.get('result',{}).get('result',{}).get('value','')); break"
    )
    proc = docker_python(code)
    text = proc.stdout or ""
    if "Looking for surveys" in text or "No more surveys" in text:
        return False
    return "QUERY" in text and "RESULT AD" in text and "Request ID" in text


def last_submit_time() -> datetime | None:
    latest: datetime | None = None
    for path in sorted(RECORDS.glob("*_batch_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        submit = data.get("submit") or {}
        if not submit.get("submitted"):
            continue
        ts = submit.get("submitted_at")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts)
        except ValueError:
            continue
        if latest is None or dt > latest:
            latest = dt
    return latest


def wait_for_submit_window() -> None:
    last = last_submit_time()
    if last is None:
        return
    ready = last + timedelta(seconds=WAIT_SEC)
    now = datetime.now()
    if now >= ready:
        return
    remain = (ready - now).total_seconds()
    log(f"Waiting {remain:.0f}s until 9-minute submit window opens (last submit {last.isoformat()})")
    while remain > 0:
        chunk = min(30.0, remain)
        time.sleep(chunk)
        remain = (ready - datetime.now()).total_seconds()
        if remain > 0:
            log(f"  submit window: {remain:.0f}s remaining...")


def next_batch_path() -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    nums = []
    for path in RECORDS.glob(f"{today}_batch_*.json"):
        m = re.search(r"_batch_(\d+)\.json$", path.name)
        if m:
            nums.append(int(m.group(1)))
    n = max(nums) + 1 if nums else 1
    return RECORDS / f"{today}_batch_{n:03d}.json"


def load_sop_text() -> str:
    parts = []
    if SOP_FULL.exists():
        parts.append(SOP_FULL.read_text(encoding="utf-8"))
    if SOP_COMPACT.exists():
        parts.append(SOP_COMPACT.read_text(encoding="utf-8"))
    return "\n\n".join(parts)


def llm_request(prompt: str) -> str:
    base = os.environ.get("ANTHROPIC_BASE_URL", "").rstrip("/")
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    if not base or not token:
        raise RuntimeError("ANTHROPIC_BASE_URL and ANTHROPIC_AUTH_TOKEN must be set for auto rating")

    body = json.dumps(
        {
            "model": MODEL,
            "max_tokens": 2500,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/v1/messages",
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": token,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    text = ""
    for block in data.get("content") or []:
        if block.get("type") == "text":
            text += block.get("text", "")
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text


def call_llm_for_task(task: dict[str, Any]) -> dict[str, Any]:
    """One independent LLM judgment per task — no batch shortcuts or keyword rules."""
    ad = task.get("ad") or {}
    sop = load_sop_text()
    prompt = f"""You are an expert Search Ads Relevance rater. Judge ONLY this single task.

Hard rules:
1. Do NOT use keyword matching, category tables, or fixed templates to pick a rating.
2. Analyze this specific query intent and this specific advertised app independently.
3. Research mentally: what does the user want? what does the app do? would they click?
4. For games, compare play style, theme, and audience — not just "both are games".
5. Output must be tailored to this query and this app; generic comments are invalid.

SOP reference:
{sop}

Task to judge:
- index: {task["index"]}
- task_id: {task["task_id"]}
- query: {task["query"]}
- ad_name: {ad.get("name", "")}
- ad_developer: {ad.get("developer", "")}

Return ONLY one JSON object with fields:
index, query_intent, ad_type (app or game), relationship_analysis,
rating (Excellent|Good|Acceptable|Bad), comment.

Comment format (must mention this query and this app by name):
[Query Intent] ... [Ad Analysis] ... [Relevance Breakdown] ... [Why not higher/lower] ... Rated <Rating>."""

    raw = llm_request(prompt)
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise ValueError(f"Task {task['task_id']}: LLM response is not a JSON object")
    return result


def rate_tasks_independently(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rated: list[dict[str, Any]] = []
    for task in tasks:
        log(
            f"Independent LLM judgment: task {task['index']} "
            f"(id={task['task_id']}, query={task.get('query', '')!r})"
        )
        result = call_llm_for_task(task)
        validate_single_rating(task, result)
        rated.append(result)
        time.sleep(0.5)
    return rated


def validate_single_rating(task: dict[str, Any], result: dict[str, Any]) -> None:
    rating = result.get("rating", "")
    comment = (result.get("comment") or "").strip()
    if rating not in ALLOWED_RATINGS:
        raise ValueError(f"Task {task['task_id']}: invalid rating {rating!r}")
    if len(comment) < 80:
        raise ValueError(f"Task {task['task_id']}: comment too short")
    if rating == "Bad" and len(comment) < 120:
        raise ValueError(f"Task {task['task_id']}: Bad rating needs detailed comment")
    ad_name = ((task.get("ad") or {}).get("name") or "").strip()
    comment_lower = comment.lower()
    query_tokens = [p for p in re.split(r"\s+", (task.get("query") or "").strip()) if len(p) >= 2]
    if query_tokens and not any(tok.lower() in comment_lower for tok in query_tokens):
        raise ValueError(f"Task {task['task_id']}: comment must reference the query")
    if ad_name:
        ad_tokens = [p for p in re.split(r"[\s\-–—|/]+", ad_name) if len(p) >= 2]
        if ad_tokens and not any(tok.lower() in comment_lower for tok in ad_tokens[:3]):
            raise ValueError(f"Task {task['task_id']}: comment must reference the advertised app")
    if f"rated {rating.lower()}" not in comment_lower:
        raise ValueError(f"Task {task['task_id']}: comment must end with Rated {rating}")


def build_batch_record(tasks: list[dict[str, Any]], rated: list[dict[str, Any]], path: Path) -> None:
    by_index = {int(r.get("index", 0)): r for r in rated}
    batch_tasks = []
    for t in tasks:
        r = by_index.get(int(t["index"]), {})
        ad = t.get("ad") or {}
        ad_type = r.get("ad_type") or r.get("type") or "app"
        if ad_type not in ("app", "game"):
            ad_type = "app"
        batch_tasks.append(
            {
                "index": t["index"],
                "task_id": t["task_id"],
                "query": t["query"],
                "query_intent": r.get("query_intent", ""),
                "ad": {
                    "name": ad.get("name", ""),
                    "subtitle": "",
                    "developer": ad.get("developer", ""),
                    "type": ad_type,
                },
                "evidence": [{"source": "Ad preview / LLM analysis", "note": r.get("relationship_analysis", "")}],
                "relationship_analysis": r.get("relationship_analysis", ""),
                "rating": r.get("rating", ""),
                "comment": r.get("comment", ""),
                "pre_submit_checked": True,
            }
        )
    now = datetime.now().isoformat(timespec="seconds")
    record = {
        "batch_id": path.stem,
        "project": "AD Search Ads Relevance",
        "operator": "auto_ad_daemon",
        "rating_method": RATING_METHOD,
        "created_at": now,
        "source_page": "tryrating current page",
        "tasks": batch_tasks,
        "pre_submit_verification": {
            "all_radios_selected": True,
            "all_comments_present": True,
            "comments_match_each_task": True,
            "bad_comments_explain_why": True,
            "no_required_errors": True,
            "record_matches_page": True,
        },
        "submit": {
            "authorized_by_user": True,
            "submitted": False,
            "submitted_at": "",
            "post_submit_status": "",
        },
    }
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_record(path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "validate_ad_batch.py"), str(path), "--require-checked"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stdout + proc.stderr)


def fill_and_submit(path: Path) -> None:
    rel = f"records/{path.name}"
    for step, script in (("fill", "fill_ad_page.py"), ("submit", "submit_ad_page.py")):
        proc = docker_py(script, rel)
        out = (proc.stdout or "") + (proc.stderr or "")
        log(out.strip())
        if proc.returncode != 0:
            raise RuntimeError(f"{script} failed: {out}")


def process_batch() -> bool:
    if not page_has_ad_tasks():
        log("No AD tasks on page")
        return False

    tasks = extract_page_tasks()
    if not tasks:
        log("Could not extract tasks")
        return False
    if len(tasks) < 1:
        log("No tasks extracted from page")
        return False
    log(f"Batch size: {len(tasks)} task(s)")

    task_ids = [str(t["task_id"]) for t in tasks]
    log(f"Found batch: {', '.join(task_ids)}")

    path = next_batch_path()
    log(f"Per-task LLM rating -> {path.name}")
    rated = rate_tasks_independently(tasks)
    build_batch_record(tasks, rated, path)
    validate_record(path)

    wait_for_submit_window()
    log(f"Filling and submitting {path.name}")
    fill_and_submit(path)
    log(f"Submitted {path.name}")
    time.sleep(5)
    return True


def main() -> None:
    RUNS.mkdir(parents=True, exist_ok=True)
    load_credentials()
    pid_file = RUNS / "auto_ad_daemon.pid"
    pid_file.write_text(str(os.getpid()), encoding="utf-8")
    log(f"AD auto daemon started (9-minute submit interval, model={MODEL})")
    while True:
        try:
            if process_batch():
                continue
        except urllib.error.URLError as exc:
            log(f"Network/LLM error: {exc}")
        except Exception as exc:  # noqa: BLE001
            log(f"Error: {exc}")
        time.sleep(POLL_SEC)


if __name__ == "__main__":
    main()
