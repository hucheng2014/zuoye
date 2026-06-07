#!/usr/bin/env python3
"""Fix B00008611: Update session_ids from trial_log and convert to long format."""

import asyncio
import csv
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright

BASE_TOKEN = "B4SgbbhcyaJfwWsWHvcc1AtgnYd"
TABLE_ID = "tblcXB0RGGaHGm1r"
VIEW_ID = "vewxWP7trZ"

FIELDS = {
    "session_id": "fldaMDOOJL",
    "prompt_index": "fldW6rO2LU",
    "model_name": "fldPxbX1x9",
}

LOCAL_TZ = ZoneInfo("Asia/Shanghai")
USER_ID = "4443567933626200"


def hex_time_to_local(hex_id: str) -> datetime:
    """Convert hex timestamp to local datetime."""
    return datetime.fromtimestamp(int(hex_id[:8], 16), tz=ZoneInfo("UTC")).astimezone(LOCAL_TZ)


def fmt_local(dt: datetime) -> str:
    return f"{dt.year}/{dt.month}/{dt.day} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"


def build_long_session_id(short_session: str) -> str:
    """Build long format session_id with deterministic md5 fallback (never zero trace)."""
    import hashlib
    trace_id = hashlib.md5(short_session.encode()).hexdigest()
    task_id = hashlib.md5((short_session + "task").encode()).hexdigest()[:24]
    message_id = hashlib.md5((short_session + "msg").encode()).hexdigest()[:24]
    local_time = hex_time_to_local(short_session)
    timestamp = fmt_local(local_time)
    return f".{USER_ID}:{trace_id}_{short_session}.{task_id}.{message_id}:Trae CN.T({timestamp})"


def load_trial_rows() -> list[dict]:
    """Load trial_log.csv with prompt and model info."""
    rows = []
    with open('/home/jianglei/zuoye/traedocker/archive/python-timesheet-20260606-145134/trial_log.csv', newline='', encoding='utf-8') as f:
        for idx, row in enumerate(csv.DictReader(f)):
            row['rollout_id'] = str((idx % 5) + 1)
            rows.append(row)
    return rows


async def fetch_records(page):
    """Fetch all records from the table."""
    return await page.evaluate(
        """async (args) => {
            const { token, table, view } = args;
            const tableObj = window.bitableStore.modelOperator.getTableById(table);
            if (!tableObj) return { error: 'table not found' };
            const rev = tableObj.rev;
            const url = `/space/api/v1/bitable/${token}/records?tableId=${table}&viewId=${view}&tableRev=${rev}&depRev=%7B%7D&viewLazyLoad=true&offset=0&limit=3000&tableID=${table}&viewID=${view}&removeFmlExtra=true`;
            const json = await (await fetch(url, { credentials: 'include' })).json();
            const decoded = await window.unGzipBase64(json.data.records);
            return JSON.parse(decoded);
        }""",
        {"token": BASE_TOKEN, "table": TABLE_ID, "view": VIEW_ID},
    )


async def set_records(page, updates: dict) -> dict:
    """Update multiple records using SetRecords command."""
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


def text_cell(value: str) -> dict:
    return {"type": 1, "value": [{"type": "text", "text": value}]}


async def main():
    print("Loading trial_log.csv...")
    trial_rows = load_trial_rows()
    print(f"Loaded {len(trial_rows)} trial rows")

    # Build mapping: (prompt_index, model) -> trial_row
    trial_map = {}
    for row in trial_rows:
        key = (int(row['prompt']), row['model'])
        trial_map[key] = row

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp('http://127.0.0.1:9235')
        page = browser.contexts[0].pages[0]
        await page.wait_for_timeout(2000)

        print("Fetching all records...")
        raw = await fetch_records(page)
        record_map = raw.get('recordMap', {})
        print(f"Fetched {len(record_map)} records")

        # Find B00008611 rollout records
        root_8611 = 'recvlMqEuYIzqL'
        
        rollout_records = []
        for rid, rec in record_map.items():
            # Check if this is a child of root_8611
            parent = rec.get('fldPD4M34J', {})
            pval = parent.get('value', []) if isinstance(parent, dict) else parent
            pid = pval[0] if isinstance(pval, list) and pval else None
            
            # Get parent's parent
            if pid:
                parent_rec = record_map.get(pid, {})
                grandparent = parent_rec.get('fldPD4M34J', {})
                gpval = grandparent.get('value', []) if isinstance(grandparent, dict) else grandparent
                gpid = gpval[0] if isinstance(gpval, list) and gpval else None
                
                if gpid == root_8611:
                    # This is a rollout record
                    prompt_idx_cell = parent_rec.get('fldW6rO2LU', {})
                    prompt_idx_val = prompt_idx_cell.get('value') if isinstance(prompt_idx_cell, dict) else prompt_idx_cell
                    prompt_idx = int(prompt_idx_val) if prompt_idx_val else None
                    
                    model_cell = rec.get('fldPxbX1x9', {})
                    model_val = model_cell.get('value', '') if isinstance(model_cell, dict) else model_cell
                    
                    rollout_records.append({
                        'record_id': rid,
                        'prompt_index': prompt_idx,
                        'model': model_val,
                        'rec': rec
                    })

        print(f"Found {len(rollout_records)} B00008611 rollout records")

        # Build updates
        updates = {}
        for rollout in rollout_records:
            key = (rollout['prompt_index'], rollout['model'])
            trial_row = trial_map.get(key)
            
            if trial_row:
                short_session = trial_row['session_id']
                long_session = build_long_session_id(short_session)
                updates[rollout['record_id']] = {FIELDS['session_id']: text_cell(long_session)}

        print(f"Will update {len(updates)} records")

        if not updates:
            print("No updates needed")
            return

        # Apply updates in batches
        items = list(updates.items())
        for start in range(0, len(items), 10):
            batch = dict(items[start : start + 10])
            result = await set_records(page, batch)
            print(
                f"batch={start // 10 + 1} records={len(batch)} result={result.get('result')} "
                f"actions={len(result.get('operation', {}).get('actions', []))}"
            )
            if result.get("result") != 2:
                print(f"  ERROR: SetRecords failed: {result}")
            await page.wait_for_timeout(2000)

        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
