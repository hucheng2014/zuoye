#!/usr/bin/env python3
"""Upload 35 git_diff patches for B00008611."""

import asyncio
import csv
import base64
from pathlib import Path
from playwright.async_api import async_playwright

BASE_TOKEN = "B4SgbbhcyaJfwWsWHvcc1AtgnYd"
TABLE_ID = "tblcXB0RGGaHGm1r"
VIEW_ID = "vewxWP7trZ"

F_GIT_DIFF = "fld3Jhw2G1"
F_PROMPT = "fldW6rO2LU"
F_ROLLOUT = "fldqgS0GPQ"
F_PARENT = "fldPD4M34J"

ROOT_8611 = "recvlMqEuYIzqL"
PATCH_DIR = Path("/home/jianglei/zuoye/traedocker/archive/python-timesheet-20260606-145134")


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


def load_trial_rows():
    rows = []
    with open(PATCH_DIR / "trial_log.csv", newline="", encoding="utf-8") as f:
        for idx, row in enumerate(csv.DictReader(f)):
            row["rollout_id"] = str((idx % 5) + 1)
            rows.append(row)
    return rows


async def upload_attachment(page, record_id, field_id, file_path):
    """Upload a single attachment using the Bitable API."""
    file_bytes = file_path.read_bytes()
    file_b64 = base64.b64encode(file_bytes).decode("ascii")
    
    result = await page.evaluate(
        """async (a) => {
            // Upload file first
            const uploadUrl = `/space/api/v1/bitable/${a.token}/upload`;
            const uploadBody = {
                table: a.table,
                view: a.view,
                recordId: a.recordId,
                fieldId: a.fieldId,
                fileName: a.fileName,
                fileSize: a.fileSize,
                fileBase64: a.fileBase64,
            };
            const uploadJson = await (await fetch(uploadUrl, {
                method: 'POST',
                credentials: 'include',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(uploadBody),
            })).json();
            
            if (uploadJson.code !== 0) return uploadJson;
            
            // Set the attachment
            const setUrl = `/space/api/v1/bitable/${a.token}/records`;
            const setBody = {
                table: a.table,
                view: a.view,
                recordIds: [a.recordId],
                records: [{
                    recordId: a.recordId,
                    fields: {
                        [a.fieldId]: {type: 17, value: [{attachmentToken: uploadJson.data.token}]}
                    }
                }]
            };
            const setJson = await (await fetch(setUrl, {
                method: 'POST',
                credentials: 'include',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(setBody),
            })).json();
            return setJson;
        }""",
        {
            "token": BASE_TOKEN,
            "table": TABLE_ID,
            "view": VIEW_ID,
            "recordId": record_id,
            "fieldId": field_id,
            "fileName": file_path.name,
            "fileSize": len(file_bytes),
            "fileBase64": file_b64,
        },
    )
    return result


async def main():
    trial_rows = load_trial_rows()
    trial_map = {}
    for r in trial_rows:
        trial_map[(int(r["prompt"]), r["rollout_id"])] = r

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

        # Find B00008611 rollout records
        targets = []
        for rid, rec in rm.items():
            pid = get_parent_id(rec)
            if not pid:
                continue
            prec = rm.get(pid, {})
            gpid = get_parent_id(prec)
            if gpid != ROOT_8611:
                continue

            prompt_cell = prec.get(F_PROMPT, {})
            prompt_val = prompt_cell.get("value") if isinstance(prompt_cell, dict) else prompt_cell
            if prompt_val is None:
                continue

            rollout_val = unwrap_text(rec.get(F_ROLLOUT)).strip()
            if not rollout_val:
                continue

            key = (int(prompt_val), rollout_val)
            trial_row = trial_map.get(key)
            if not trial_row:
                print(f"WARN: no trial row for {key}")
                continue

            patch_file = PATCH_DIR / trial_row["patch_file"]
            if not patch_file.exists():
                print(f"WARN: patch file missing: {patch_file}")
                continue

            # Check if already has attachment
            git_diff_cell = rec.get(F_GIT_DIFF, {})
            git_diff_val = git_diff_cell.get("value", []) if isinstance(git_diff_cell, dict) else git_diff_cell
            if git_diff_val:
                continue

            targets.append((rid, patch_file))

        print(f"Will upload {len(targets)} patches")

        for i, (rid, patch_file) in enumerate(targets):
            result = await upload_attachment(page, rid, F_GIT_DIFF, patch_file)
            status = "✓" if result.get("result") == 2 or result.get("code") == 0 else "✗"
            print(f"  [{i+1}/{len(targets)}] {status} {patch_file.name} -> {rid}")
            await page.wait_for_timeout(500)

        print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
