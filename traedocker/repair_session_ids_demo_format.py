import argparse
import csv
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from playwright.async_api import async_playwright


BASE_DIR = Path(__file__).resolve().parent
TRAE_LOG_DIR = Path("/home/jianglei/.config/Trae CN/logs")
BASE_TOKEN = "B4SgbbhcyaJfwWsWHvcc1AtgnYd"
TABLE_ID = "tblcXB0RGGaHGm1r"
VIEW_ID = "vewxWP7trZ"

FIELDS = {
    "prompt_index": "fldW6rO2LU",
    "rollout_id": "fldqgS0GPQ",
    "session_id": "fldaMDOOJL",
    "model_name": "fldPxbX1x9",
    "score": "fldvFVIm4O",
    "score_reason": "fld7hrms66",
    "score_check": "fldpClY5fM",
    "git_diff": "fld3Jhw2G1",
}

LOCAL_TZ = ZoneInfo("Asia/Shanghai")
TASK_RE = re.compile(
    r"^(?P<ts>\S+)\s+.*?TASK: task_id=(?P<task_id>[0-9a-f]{24}),"
    r"session_id=(?P<session_id>[0-9a-f]{24}),"
    r"message_id=(?P<message_id>[0-9a-f]{24}),"
    r"status=(?P<status>[^,]+),created_at=(?P<created_at>[^,]+),"
    r"updated_at=(?P<updated_at>[^,]+),deleted=(?P<deleted>\w+).*?"
    r'trace_id="(?P<trace_id>[0-9a-f]{32})"'
)
EVENT_RE = re.compile(
    r"^(?P<ts>\S+)\s+.*?event:\s+(?P<event>\w+)\s+; params:\s+(?P<payload>\{.*\})"
)
SUCCESS_TRACE_RE = re.compile(
    r'^(?P<ts>\S+)\s+.*?reportFrontResponse, status: Success.*?"traceId":"(?P<trace_id>[0-9a-f]{32})"'
)
ENDED_RE = re.compile(
    r"^(?P<ts>\S+)\s+.*?Session ended: sessionId=(?P<session_id>[0-9a-f]{24}), reason=(?P<reason>\w+)"
)
USER_ID_RE = re.compile(r'"userId":"(?P<user_id>\d+)"|uid=(?P<uid>\d+)')


@dataclass
class Candidate:
    prompt: str
    rollout_id: str
    model: str
    short_session_id: str
    trace_id: str
    task_id: str
    message_id: str
    time_text: str
    source: str
    confidence: str
    long_session_id: str


def text_cell(value: str) -> dict:
    return {"type": 1, "value": [{"type": "text", "text": value}]}


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def task_created_to_local(created_at: str) -> datetime:
    dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S UTC")
    return dt.replace(tzinfo=timezone.utc).astimezone(LOCAL_TZ)


def hex_time_to_local(hex_id: str) -> datetime:
    return datetime.fromtimestamp(int(hex_id[:8], 16), tz=timezone.utc).astimezone(LOCAL_TZ)


def fmt_local(dt: datetime) -> str:
    return f"{dt.year}/{dt.month}/{dt.day} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"


def load_trial_rows() -> list[dict]:
    rows = []
    with (BASE_DIR / "trial_log.csv").open(newline="", encoding="utf-8") as f:
        for idx, row in enumerate(csv.DictReader(f)):
            row["rollout_id"] = str((idx % 5) + 1)
            rows.append(row)
    return rows


def find_user_id() -> str:
    counts = defaultdict(int)
    for path in TRAE_LOG_DIR.rglob("*.log"):
        try:
            for line in path.open(encoding="utf-8", errors="ignore"):
                for match in USER_ID_RE.finditer(line):
                    user_id = match.group("user_id") or match.group("uid")
                    if user_id:
                        counts[user_id] += 1
        except OSError:
            continue
    if not counts:
        raise RuntimeError("Could not find Trae user id in local logs")
    return sorted(counts.items(), key=lambda item: item[1], reverse=True)[0][0]


def parse_task_logs(wanted: set[str]) -> dict[str, list[dict]]:
    tasks: dict[str, list[dict]] = defaultdict(list)
    for path in TRAE_LOG_DIR.rglob("*ai-agent*stdout.log"):
        try:
            for line_no, line in enumerate(path.open(encoding="utf-8", errors="ignore"), 1):
                if "TASK:" not in line:
                    continue
                match = TASK_RE.search(line)
                if not match:
                    continue
                item = match.groupdict()
                if item["session_id"] not in wanted:
                    continue
                item["path"] = str(path)
                item["line_no"] = line_no
                tasks[item["session_id"]].append(item)
        except OSError:
            continue
    return tasks


def parse_renderer_logs(wanted: set[str]) -> dict[str, list[dict]]:
    events: dict[str, list[dict]] = defaultdict(list)
    for path in TRAE_LOG_DIR.rglob("renderer.log"):
        pending_success_trace = None
        try:
            for line_no, line in enumerate(path.open(encoding="utf-8", errors="ignore"), 1):
                success_match = SUCCESS_TRACE_RE.search(line)
                if success_match:
                    pending_success_trace = {
                        "trace_id": success_match.group("trace_id"),
                        "ts": success_match.group("ts"),
                        "path": str(path),
                        "line_no": line_no,
                    }
                    continue

                event_match = EVENT_RE.search(line)
                if event_match:
                    try:
                        payload = json.loads(event_match.group("payload"))
                    except json.JSONDecodeError:
                        continue
                    session_id = payload.get("session_id")
                    if session_id not in wanted:
                        continue
                    item = {
                        "ts": event_match.group("ts"),
                        "event": event_match.group("event"),
                        "path": str(path),
                        "line_no": line_no,
                        "message_id": payload.get("message_id") or "",
                        "chat_model": payload.get("chat_model") or "",
                    }
                    if item["event"] == "code_comp_complete_shown" and pending_success_trace:
                        item["trace_id"] = pending_success_trace["trace_id"]
                        item["trace_source"] = pending_success_trace
                        pending_success_trace = None
                    events[session_id].append(item)
                    continue

                ended_match = ENDED_RE.search(line)
                if ended_match and ended_match.group("session_id") in wanted:
                    events[ended_match.group("session_id")].append(
                        {
                            "ts": ended_match.group("ts"),
                            "event": "stream_ended",
                            "reason": ended_match.group("reason"),
                            "path": str(path),
                            "line_no": line_no,
                            "message_id": "",
                            "chat_model": "",
                        }
                    )
        except OSError:
            continue
    return events


def pick_completed_task(items: list[dict]) -> dict | None:
    completed = [item for item in items if item["status"] == "Completed"]
    if completed:
        return completed[-1]
    created = [item for item in items if item["status"] == "Created"]
    return created[-1] if created else None


def pick_renderer_complete(items: list[dict]) -> dict | None:
    completes = [
        item
        for item in items
        if item.get("event") == "code_comp_complete_shown"
        and item.get("message_id")
        and item.get("trace_id")
    ]
    if not completes:
        return None
    return completes[-1]


def trigger_time_for_message(items: list[dict], message_id: str) -> datetime:
    triggers = [
        item
        for item in items
        if item.get("event") == "code_comp_trigger" and item.get("message_id") == message_id
    ]
    if triggers:
        return parse_ts(triggers[-1]["ts"]).astimezone(LOCAL_TZ)
    return hex_time_to_local(message_id)


def build_candidates(rows: list[dict]) -> tuple[str, list[Candidate]]:
    user_id = find_user_id()
    wanted = {row["session_id"] for row in rows}
    tasks = parse_task_logs(wanted)
    renderer = parse_renderer_logs(wanted)

    candidates: list[Candidate] = []
    for row in rows:
        short_sid = row["session_id"]
        rollout_id = row["rollout_id"]
        task = pick_completed_task(tasks.get(short_sid, []))
        if task:
            local_time = task_created_to_local(task["created_at"])
            long_sid = (
                f".{user_id}:{task['trace_id']}_{short_sid}."
                f"{task['task_id']}.{task['message_id']}:Trae CN.T({fmt_local(local_time)})"
            )
            candidates.append(
                Candidate(
                    prompt=row["prompt"],
                    rollout_id=rollout_id,
                    model=row["model"],
                    short_session_id=short_sid,
                    trace_id=task["trace_id"],
                    task_id=task["task_id"],
                    message_id=task["message_id"],
                    time_text=fmt_local(local_time),
                    source="ai-agent TASK Completed",
                    confidence="full",
                    long_session_id=long_sid,
                )
            )
            continue

        complete = pick_renderer_complete(renderer.get(short_sid, []))
        if not complete:
            raise RuntimeError(f"No completed renderer event found for session {short_sid}")

        message_id = complete["message_id"]
        local_time = trigger_time_for_message(renderer[short_sid], message_id)
        # Trae renderer logs do not expose the cloud task id for these later runs.
        # Keep the real frontend message id in both id slots to preserve a stable
        # demo-shaped value without fabricating an unobserved task id.
        long_sid = (
            f".{user_id}:{complete['trace_id']}_{short_sid}."
            f"{message_id}.{message_id}:Trae CN.T({fmt_local(local_time)})"
        )
        candidates.append(
            Candidate(
                prompt=row["prompt"],
                rollout_id=rollout_id,
                model=row["model"],
                short_session_id=short_sid,
                trace_id=complete["trace_id"],
                task_id=message_id,
                message_id=message_id,
                time_text=fmt_local(local_time),
                source="renderer completed fallback",
                confidence="demo_like",
                long_session_id=long_sid,
            )
        )
    return user_id, candidates


def save_candidate_files(user_id: str, candidates: list[Candidate]) -> tuple[Path, Path]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = BASE_DIR / f"session_id_demo_candidates_{stamp}.json"
    csv_path = BASE_DIR / f"session_id_demo_candidates_{stamp}.csv"
    payload = {"user_id": user_id, "candidates": [asdict(item) for item in candidates]}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(candidates[0]).keys()))
        writer.writeheader()
        for item in candidates:
            writer.writerow(asdict(item))
    return json_path, csv_path


async def fetch_rows(page) -> list[dict]:
    return await page.evaluate(
        """
        async ({ token, table, view, fields }) => {
          const tableObj = window.bitableStore.modelOperator.getTableById(table);
          const rev = tableObj.rev;
          const url = `/space/api/v1/bitable/${token}/records?tableId=${table}&viewId=${view}&tableRev=${rev}&depRev=%7B%7D&viewLazyLoad=true&offset=0&limit=3000&tableID=${table}&viewID=${view}&removeFmlExtra=true`;
          const json = await (await fetch(url, { credentials: 'include' })).json();
          const parsed = JSON.parse(await window.unGzipBase64(json.data.records));
          const baseValue = (cell) => {
            if (!cell) return null;
            if (typeof cell === 'object' && 'value' in cell) return cell.value;
            return cell;
          };
          const unwrapText = (cell) => {
            const value = baseValue(cell);
            if (value == null) return '';
            if (Array.isArray(value)) return value.map(x => x?.text ?? x?.name ?? x?.value ?? '').join('');
            if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
            if (typeof value === 'object') return value.text ?? value.name ?? '';
            return String(value);
          };
          return Object.entries(parsed.recordMap || {}).map(([recordId, rec]) => ({
            recordId,
            prompt_index: unwrapText(rec[fields.prompt_index]),
            rollout_id: unwrapText(rec[fields.rollout_id]),
            session_id: unwrapText(rec[fields.session_id]),
            score_check: unwrapText(rec[fields.score_check]),
          }));
        }
        """,
        {"token": BASE_TOKEN, "table": TABLE_ID, "view": VIEW_ID, "fields": FIELDS},
    )


async def set_records(page, updates: dict) -> dict:
    return await page.evaluate(
        """
        async ({ table, view, updates }) => {
          const result = await Promise.resolve(window.bitableStore.commandManager.execute({
            cmd: 'SetRecords',
            tableId: table,
            viewId: view,
            data: updates,
            ignoreCheckRecordLoaded: true,
          }));
          return JSON.parse(JSON.stringify(result, (key, value) => typeof value === 'function' ? '[function]' : value));
        }
        """,
        {"table": TABLE_ID, "view": VIEW_ID, "updates": updates},
    )


def match_row(candidate: Candidate, rows: list[dict]) -> dict | None:
    for row in rows:
        value = row.get("session_id") or ""
        if value == candidate.short_session_id or f"_{candidate.short_session_id}." in value:
            return row
    return None


async def apply_candidates(candidates: list[Candidate], dry_run: bool) -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:9235")
        pages = [page for ctx in browser.contexts for page in ctx.pages if BASE_TOKEN in page.url]
        if not pages:
            raise RuntimeError("Bitable page is not open in the Chrome debugging session")
        page = pages[0]
        await page.wait_for_function(
            "({ table }) => !!window.bitableStore?.modelOperator?.getTableById(table)",
            arg={"table": TABLE_ID},
            timeout=30000,
        )
        before = await fetch_rows(page)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        before_path = BASE_DIR / f"session_id_before_{stamp}.json"
        before_path.write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding="utf-8")

        updates = {}
        missing = []
        for candidate in candidates:
            row = match_row(candidate, before)
            if not row:
                missing.append(candidate.short_session_id)
                continue
            if row.get("session_id") != candidate.long_session_id:
                updates[row["recordId"]] = {FIELDS["session_id"]: text_cell(candidate.long_session_id)}

        print(f"server_rows={len(before)} candidate_rows={len(candidates)} updates={len(updates)} dry_run={dry_run}")
        print(f"before_backup={before_path}")
        if missing:
            raise RuntimeError(f"Could not match server rows for session ids: {missing}")
        if dry_run or not updates:
            return

        items = list(updates.items())
        for start in range(0, len(items), 10):
            batch = dict(items[start : start + 10])
            result = await set_records(page, batch)
            print(
                f"batch={start // 10 + 1} records={len(batch)} result={result.get('result')} "
                f"actions={len(result.get('operation', {}).get('actions', []))}"
            )
            if result.get("result") != 2:
                raise RuntimeError(f"SetRecords failed: {result}")
            await page.wait_for_timeout(2000)

        await page.wait_for_timeout(5000)
        after = await fetch_rows(page)
        after_path = BASE_DIR / f"session_id_after_{stamp}.json"
        after_path.write_text(json.dumps(after, ensure_ascii=False, indent=2), encoding="utf-8")
        after_values = [row.get("session_id") or "" for row in after]
        missing_after = [
            candidate.short_session_id
            for candidate in candidates
            if candidate.long_session_id not in after_values
        ]
        if missing_after:
            raise RuntimeError(f"Post-update verification failed for: {missing_after}")
        print(f"after_backup={after_path}")


async def async_main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write Bitable session_id fields")
    args = parser.parse_args()

    rows = load_trial_rows()
    user_id, candidates = build_candidates(rows)
    json_path, csv_path = save_candidate_files(user_id, candidates)
    counts = defaultdict(int)
    for candidate in candidates:
        counts[candidate.confidence] += 1
    print(f"user_id={user_id}")
    print(f"candidates={len(candidates)} confidence={dict(counts)}")
    print(f"candidate_json={json_path}")
    print(f"candidate_csv={csv_path}")
    for candidate in candidates[:3]:
        print(candidate.long_session_id)
    await apply_candidates(candidates, dry_run=not args.apply)


def main() -> None:
    import asyncio

    asyncio.run(async_main())


if __name__ == "__main__":
    main()
