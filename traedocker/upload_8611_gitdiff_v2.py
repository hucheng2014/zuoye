#!/usr/bin/env python3
"""Upload 35 git_diff patches for B00008611 using Drive SDK."""

import asyncio
import csv
import json
import mimetypes
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


async def upload_drive_file(page, file_path: Path) -> dict:
    """Upload file to Drive and return token."""
    input_handle = await page.evaluate_handle("""() => {
        let input = document.querySelector('#upload-input');
        if (!input) {
            input = document.createElement('input');
            input.type = 'file';
            input.id = 'upload-input';
            input.style.position = 'fixed';
            input.style.left = '-10000px';
            document.body.appendChild(input);
        }
        input.value = '';
        return input;
    }""")
    element = input_handle.as_element()
    await element.set_input_files(str(file_path))
    
    result = await page.evaluate("""async ({ table }) => {
        const input = document.querySelector('#upload-input');
        const file = input?.files?.[0];
        if (!file) throw new Error('no file');

        const { SuiteUploader } = await window.BitableDep.DriveHelper.getUploadSDK();
        const uploader = new SuiteUploader({
            envConfigs: window.BitableDep.DriveHelper.getUploadSDKEnvConfig(),
            featureFlags: {
                smallFileDirectUpload: true,
                largeFileFastUpload: false,
                fileSizeChecker: false,
                concurrentAndRetryableUpload: false,
            },
            maxSimultaneousUploads: 1,
            riskDetectionExtra: window.BitableDep.DriveHelper.getUploadRiskDetectionExtra(),
        });
        
        const opts = {
            jobType: 1,
            parentToken: window.bitableStore.token,
            mountPoint: 'bitable',
            businessType: 1,
            shouldAddToRecents: false,
            sizeLimit: 1024 * 1024 * 1024,
            bizExtra: { extra: JSON.stringify({ table_id: table }) },
            bizPayload: { source: 'git_diff_upload' },
            riskDetectionExtra: window.BitableDep.DriveHelper.getUploadRiskDetectionExtra(),
        };
        
        const taskId = await uploader.loadFile(file, opts);
        uploader.upload();
        
        const deadline = Date.now() + 60000;
        while (Date.now() < deadline) {
            const task = (uploader.tasks || []).find(t => t.id === taskId) || uploader.tasks?.[0];
            if (task?.status === 3 && task.token) {
                return { ok: true, token: task.token, name: file.name, size: file.size, mimeType: file.type };
            }
            if (task?.status === 4 || task?.error) {
                return { ok: false, error: task.error || 'upload failed' };
            }
            await new Promise(r => setTimeout(r, 500));
        }
        return { ok: false, error: 'timeout' };
    }""", {"table": TABLE_ID})
    
    if not result.get("ok"):
        raise RuntimeError(f"upload failed: {result}")
    return result


def attachment_cell(upload: dict, file_path: Path) -> dict:
    token = str(upload["token"])
    mime_type = str(upload.get("mimeType") or mimetypes.guess_type(file_path.name)[0] or "application/octet-stream")
    return {
        "type": 17,
        "value": [{
            "id": token,
            "attachmentToken": token,
            "timeStamp": int(upload.get("timeStamp") or 0),
            "name": file_path.name,
            "mimeType": mime_type,
            "size": int(upload.get("size") or file_path.stat().st_size),
        }]
    }


async def set_attachment(page, record_id: str, field_id: str, cell: dict) -> dict:
    return await page.evaluate("""({ table, view, recordId, fieldId, cell }) => {
        const result = window.bitableStore.commandManager.execute({
            cmd: 'SetRecords',
            tableId: table,
            viewId: view,
            data: { [recordId]: { [fieldId]: cell } },
            ignoreCheckRecordLoaded: true,
        });
        return JSON.parse(JSON.stringify(result, (k, v) => typeof v === 'function' ? '[fn]' : v));
    }""", {
        "table": TABLE_ID,
        "view": VIEW_ID,
        "recordId": record_id,
        "fieldId": field_id,
        "cell": cell,
    })


async def main():
    trial_rows = load_trial_rows()
    trial_map = {}
    for r in trial_rows:
        trial_map[(int(r["prompt"]), r["rollout_id"])] = r

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        page = browser.contexts[0].pages[0]
        await page.wait_for_timeout(2000)

        raw = await page.evaluate("""async (a) => {
            const t = window.bitableStore.modelOperator.getTableById(a.table);
            const r = t.rev;
            const u = `/space/api/v1/bitable/${a.token}/records?tableId=${a.table}&viewId=${a.view}&tableRev=${r}&depRev=%7B%7D&viewLazyLoad=true&offset=0&limit=3000&tableID=${a.table}&viewID=${a.view}&removeFmlExtra=true`;
            const j = await (await fetch(u, {credentials:'include'})).json();
            const d = await window.unGzipBase64(j.data.records);
            return JSON.parse(d);
        }""", {"token": BASE_TOKEN, "table": TABLE_ID, "view": VIEW_ID})
        rm = raw.get("recordMap", {})

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
                continue

            patch_file = PATCH_DIR / trial_row["patch_file"]
            if not patch_file.exists():
                continue

            git_diff_cell = rec.get(F_GIT_DIFF, {})
            git_diff_val = git_diff_cell.get("value", []) if isinstance(git_diff_cell, dict) else git_diff_cell
            if git_diff_val:
                continue

            targets.append((rid, patch_file))

        print(f"Will upload {len(targets)} patches")

        for i, (rid, patch_file) in enumerate(targets):
            try:
                upload = await upload_drive_file(page, patch_file)
                cell = attachment_cell(upload, patch_file)
                result = await set_attachment(page, rid, F_GIT_DIFF, cell)
                status = "✓" if result.get("result") == 2 else "✗"
                print(f"  [{i+1}/{len(targets)}] {status} {patch_file.name}")
                await page.wait_for_timeout(1000)
            except Exception as e:
                print(f"  [{i+1}/{len(targets)}] ✗ {patch_file.name}: {e}")

        print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
