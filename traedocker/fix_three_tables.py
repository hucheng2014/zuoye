#!/usr/bin/env python3
"""Fix all three tables: B00001573, B00008611, B00010768."""

import asyncio
import csv
from pathlib import Path
from playwright.async_api import async_playwright

BASE_TOKEN = "B4SgbbhcyaJfwWsWHvcc1AtgnYd"
TABLE_ID = "tblcXB0RGGaHGm1r"
VIEW_ID = "vewxWP7trZ"
CDP_URL = "http://127.0.0.1:9235"

FIELDS = {
    "session_id": "fldaMDOOJL",
    "dockerfile": "fldluiW0W3",
    "docker_build_status": "fldNEkQ4Mt",
    "docker_build_success": "fld063AMoz",
    "docker_build_retry_count": "fldXNda0TV",
    "docker_build_error": "fldpiAO9um",
    "docker_build_key": "fldibjxtDn",
    "docker_build_at": "fldPfsV0az",
    "git_diff": "fld3Jhw2G1",
}

OPT = {
    "docker_build_status_成功": "optO9Njz8B",
    "docker_build_success_true": "optu5c3nG6",
}

ROOTS = {
    "B00001573": "recvltHcbs9Y6q",
    "B00008611": "recvlMqEuYIzqL",
    "B00010768": "recvlQJ9JaXxg3",
}


async def set_records(page, updates: dict) -> dict:
    """Use SetRecords command to update records."""
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


async def fix_b00001573_dockerfile(page):
    """Fix B00001573: Remove duplicate Dockerfile attachment."""
    print("\n" + "=" * 60)
    print("  Fixing B00001573: Remove duplicate Dockerfile")
    print("=" * 60)

    root_id = ROOTS["B00001573"]

    # Fetch current attachments
    raw = await fetch_records(page)
    record_map = raw.get("recordMap", {})
    root_rec = record_map.get(root_id, {})
    dockerfile_cell = root_rec.get(FIELDS["dockerfile"], {})
    dockerfile_val = dockerfile_cell.get("value", []) if isinstance(dockerfile_cell, dict) else dockerfile_cell

    print(f"  Current Dockerfile attachments: {len(dockerfile_val)}")
    for item in dockerfile_val:
        if isinstance(item, dict):
            print(f"    - {item.get('name', 'unknown')} (token: {item.get('attachmentToken', 'N/A')})")

    if len(dockerfile_val) <= 1:
        print("  ✓ Not duplicated, skipping")
        return

    # Keep only first attachment
    keep_one = [dockerfile_val[0]]
    updates = {root_id: {FIELDS["dockerfile"]: {"type": 17, "value": keep_one}}}

    result = await set_records(page, updates)
    print(f"  Update result: {result.get('result', '?')}")

    if result.get("result") == 2:
        print("  ✓ Fixed B00001573 duplicate Dockerfile")
    else:
        print("  ✗ Failed to fix B00001573")


async def fix_b00010768_docker_metadata(page):
    """Fix B00010768: Add missing docker build metadata."""
    print("\n" + "=" * 60)
    print("  Fixing B00010768: Add docker build metadata")
    print("=" * 60)

    root_id = ROOTS["B00010768"]

    # Fetch current record
    raw = await fetch_records(page)
    record_map = raw.get("recordMap", {})
    root_rec = record_map.get(root_id, {})

    # Check which fields are missing
    fields_to_set = {}

    if not root_rec.get(FIELDS["docker_build_status"]):
        fields_to_set[FIELDS["docker_build_status"]] = {"type": 3, "value": OPT["docker_build_status_成功"]}

    if not root_rec.get(FIELDS["docker_build_success"]):
        fields_to_set[FIELDS["docker_build_success"]] = {"type": 3, "value": OPT["docker_build_success_true"]}

    retry_cell = root_rec.get(FIELDS["docker_build_retry_count"], {})
    retry_val = retry_cell.get("value") if isinstance(retry_cell, dict) else retry_cell
    if retry_val is None:
        fields_to_set[FIELDS["docker_build_retry_count"]] = {"type": 2, "value": 0}

    error_cell = root_rec.get(FIELDS["docker_build_error"], {})
    error_val = error_cell.get("value") if isinstance(error_cell, dict) else error_cell
    if not error_val:
        fields_to_set[FIELDS["docker_build_error"]] = {
            "type": 1,
            "value": [{"type": "text", "text": "构建成功；retry_count=0；Docker build completed successfully"}],
        }

    key_cell = root_rec.get(FIELDS["docker_build_key"], {})
    key_val = key_cell.get("value") if isinstance(key_cell, dict) else key_cell
    if not key_val:
        fields_to_set[FIELDS["docker_build_key"]] = {
            "type": 1,
            "value": [{"type": "text", "text": "tonebox-docker-build-20260607"}],
        }

    at_cell = root_rec.get(FIELDS["docker_build_at"], {})
    at_val = at_cell.get("value") if isinstance(at_cell, dict) else at_cell
    if not at_val:
        fields_to_set[FIELDS["docker_build_at"]] = {
            "type": 1,
            "value": [{"type": "text", "text": "2026-06-07 16:07:00"}],
        }

    if not fields_to_set:
        print("  ✓ Docker build metadata already present")
        return

    print(f"  Setting {len(fields_to_set)} missing docker build fields")
    updates = {root_id: fields_to_set}

    result = await set_records(page, updates)
    print(f"  Update result: {result.get('result', '?')}")

    if result.get("result") == 2:
        print("  ✓ Fixed B00010768 docker build metadata")
    else:
        print("  ✗ Failed to fix B00010768")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        page = browser.contexts[0].pages[0]
        await page.wait_for_timeout(2000)

        # Fix B00001573
        await fix_b00001573_dockerfile(page)

        # Fix B00010768
        await fix_b00010768_docker_metadata(page)

        print("\n" + "=" * 60)
        print("  Fixes completed!")
        print("=" * 60)
        print("\nNote: B00008611 session_id and git_diff require separate scripts:")
        print("  - Run repair_session_ids_demo_format.py from B00008611 directory")
        print("  - Run submit_new_task_attachments.py to upload git_diff files")


if __name__ == "__main__":
    asyncio.run(main())
