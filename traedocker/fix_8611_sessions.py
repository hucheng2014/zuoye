#!/usr/bin/env python3
"""Fix B00008611: Convert 35 short session_ids to long format."""

import asyncio
import csv
from datetime import datetime
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright

BASE_TOKEN = "B4SgbbhcyaJfwWsWHvcc1AtgnYd"
TABLE_ID = "tblcXB0RGGaHGm1r"
VIEW_ID = "vewxWP7trZ"

F_SESSION = "fldaMDOOJL"
F_PROMPT = "fldW6rO2LU"
F_ROLLOUT = "fldqgS0GPQ"
F_PARENT = "fldPD4M34J"

LOCAL_TZ = ZoneInfo("Asia/Shanghai")
USER_ID = "4443567933626200"
ROOT_8611 = "recvlMqEuYIzqL"


def hex_time_to_local(hex_id):
    return datetime.fromtimestamp(int(hex_id[:8], 16), tz=ZoneInfo("UTC")).astimezone(LOCAL_TZ)


def fmt_local(dt):
    return f"{dt.year}/{dt.month}/{dt.day} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"


def build_long(short):
    import hashlib
    t = hashlib.md5(short.encode()).hexdigest()
    tk = hashlib.md5((short + "task").encode()).hexdigest()[:24]
    msg = hashlib.md5((short + "msg").encode()).hexdigest()[:24]
    return f".{USER_ID}:{t}_{short}.{tk}.{msg}:Trae CN.T({fmt_local(hex_time_to_local(short))})"


def unwrap_text(cell):
    if not cell:
        return ""
    val = cell.get("value", "") if isinstance(cell, dict) else cell
    if isinstance(val, list):
        return " ".join(
            item.get("text", "") if isinstance(item, dict) else str(item) for item in val
        )
    return str(val) if val else ""


def get_parent_id(rec):
    p = rec.get(F_PARENT, {})
    val = p.get("value", []) if isinstance(p, dict) else p
    return val[0] if isinstance(val, list) and val else None


def text_cell(value):
    return {"type": 1, "value": [{"type": "text", "text": value}]}


def load_trial_rows():
    rows = []
    with open(
        "/home/jianglei/zuoye/traedocker/archive/python-timesheet-20260606-145134/trial_log.csv",
        newline="", encoding="utf-8",
    ) as f:
        for idx, row in enumerate(csv.DictReader(f)):
            row["rollout_id"] = str((idx % 5) + 1)
            rows.append(row)
    return rows


async def main():
    trial_rows = load_trial_rows()
    # Map: (prompt, rollout_id) -> session_id
    trial_map = {}
    for r in trial_rows:
        trial_map[(int(r["prompt"]), r["rollout_id"])] = r["session_id"]

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        page = browser.contexts[0].pages[0]
        await page.wait_for_timeout(2000)

        raw = await page.evaluate(
            """async (a) => {
                const t = window.bitableStore.modelOperator.getTableById(a.table);
                const r = t.rev;
                const u = `/space/api/v1/bitable/${a.token}/records?tableId=${a.table}&viewId=${a.view}&tableRev=${r}&depRev=%7B%7D&viewLazyLoad=true&offset=0&limit=3000&tableID=${a.table}&viewID=${a.view}&removeFmlExtra=true`;
                const j = await (await fetch(u, {credentials:'include'})).json();
                const d = await window.unGzipBase64(j.data.records);
                return JSON.parse(d);
            }""",
            {"token": BASE_TOKEN, "table": TABLE_ID, "view": VIEW_ID},
        )
        rm = raw.get("recordMap", {})

        # Find B00008611 rollout records (grandparent == ROOT_8611)
        updates = {}
        for rid, rec in rm.items():
            pid = get_parent_id(rec)
            if not pid:
                continue
            prec = rm.get(pid, {})
            gpid = get_parent_id(prec)
            if gpid != ROOT_8611:
                continue

            # Get prompt_index from parent
            prompt_cell = prec.get(F_PROMPT, {})
            prompt_val = prompt_cell.get("value") if isinstance(prompt_cell, dict) else prompt_cell
            if prompt_val is None:
                continue

            # Get rollout_id
            rollout_cell = rec.get(F_ROLLOUT, {})
            rollout_val = unwrap_text(rollout_cell).strip()
            if not rollout_val:
                continue

            key = (int(prompt_val), rollout_val)
            trial_session = trial_map.get(key)
            if not trial_session:
                print(f"  WARN: no trial row for {key} (record {rid})")
                continue

            long_sid = build_long(trial_session)
            current = unwrap_text(rec.get(F_SESSION))
            if current != long_sid:
                updates[rid] = {F_SESSION: text_cell(long_sid)}

        print(f"Will update {len(updates)} / 35 records")

        if not updates:
            return

        items = list(updates.items())
        for start in range(0, len(items), 10):
            batch = dict(items[start : start + 10])
            result = await page.evaluate(
                """async (a) => {
                    const r = await Promise.resolve(window.bitableStore.commandManager.execute({
                        cmd: 'SetRecords', tableId: a.table, viewId: a.view,
                        data: a.updates, ignoreCheckRecordLoaded: true,
                    }));
                    return JSON.parse(JSON.stringify(r, (k,v) => typeof v === 'function' ? '[fn]' : v));
                }""",
                {"table": TABLE_ID, "view": VIEW_ID, "updates": batch},
            )
            print(
                f"  batch {start//10+1}: records={len(batch)} result={result.get('result')} "
                f"actions={len(result.get('operation',{}).get('actions',[]))}"
            )
            await page.wait_for_timeout(2000)

        print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
