#!/usr/bin/env python3
"""Clear Docker build result fields on a fresh task root to retrigger system build."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

import submit_new_task_attachments as attachments
import submit_new_task_group as group


CLEAR_FIELD_TYPES = {
    "docker_build_success": 3,
    "docker_build_status": 3,
    "docker_build_retry_count": 2,
    "docker_build_log": 17,
    "docker_build_error": 1,
    "docker_build_at": 1,
    "docker_build_key": 1,
    "docker_build_screenshot": 17,
}


def empty_cell(cell_type: int) -> dict[str, Any]:
    return {"type": cell_type, "value": None}


def nonempty_build_fields(record: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field_key in CLEAR_FIELD_TYPES:
        cell = record.get(group.FIELDS[field_key])
        raw = cell.get("value") if isinstance(cell, dict) else cell
        if raw not in (None, "", []):
            result[field_key] = raw
    return result


async def run(plan_path: Path, apply: bool) -> int:
    plan = attachments.load_plan(plan_path)
    root_id = str(plan["root_id"])
    if root_id == group.OLD_ROOT_RECORD_ID:
        raise RuntimeError("refusing to clear old root record")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp(attachments.CDP_URL)
        pages = [page for ctx in browser.contexts for page in ctx.pages if group.BASE_TOKEN in page.url]
        if not pages:
            await browser.close()
            raise RuntimeError("target Bitable page is not open in the logged-in browser")
        page = pages[0]
        await page.bring_to_front()
        await page.wait_for_function(
            "({ table }) => !!window.bitableStore?.modelOperator?.getTableById(table)",
            arg={"table": group.TABLE_ID},
            timeout=30000,
        )

        before_payload = await attachments.fetch_payload(page)
        before_backup = group.write_backup(before_payload, "before_clear_docker_build_fields")
        record_map = attachments.summarize_by_id(before_payload)
        root = record_map.get(root_id)
        if not root:
            await browser.close()
            raise RuntimeError(f"fresh root record missing: {root_id}")

        before_nonempty = nonempty_build_fields(root)
        print(f"plan={plan_path}")
        print(f"root_id={root_id}")
        print(f"before_backup={before_backup}")
        print(f"fields_to_clear={sorted(CLEAR_FIELD_TYPES)}")
        print(f"nonempty_before={sorted(before_nonempty)}")
        if not apply:
            print("dry run only; pass --apply to clear fields")
            await browser.close()
            return 0

        updates = {
            group.FIELDS[field_key]: empty_cell(cell_type)
            for field_key, cell_type in CLEAR_FIELD_TYPES.items()
        }
        result = await page.evaluate(
            """
            ({ table, view, rootId, updates }) => {
              const result = window.bitableStore.commandManager.execute({
                cmd: 'SetRecords',
                tableId: table,
                viewId: view,
                data: { [rootId]: updates },
                ignoreCheckRecordLoaded: true,
              });
              return JSON.parse(JSON.stringify(result, (key, value) => {
                if (typeof value === 'function') return '[function]';
                return value;
              }));
            }
            """,
            {"table": group.TABLE_ID, "view": group.VIEW_ID, "rootId": root_id, "updates": updates},
        )
        if result.get("result") != 2:
            await browser.close()
            raise RuntimeError(f"SetRecords failed: {result}")
        await page.wait_for_timeout(3000)

        after_payload = await attachments.fetch_payload(page)
        after_backup = group.write_backup(after_payload, "after_clear_docker_build_fields")
        after_root = attachments.summarize_by_id(after_payload).get(root_id) or {}
        after_nonempty = nonempty_build_fields(after_root)
        input_files = {
            "dockerfile": attachments.cell_files(after_root, "dockerfile"),
            "repo": attachments.cell_files(after_root, "repo"),
        }

        errors: list[str] = []
        if after_nonempty:
            errors.append(f"build fields still non-empty: {sorted(after_nonempty)}")
        if "Dockerfile" not in input_files["dockerfile"]:
            errors.append(f"Dockerfile input missing after clear: {input_files['dockerfile']}")
        if "repo.zip" not in input_files["repo"]:
            errors.append(f"repo.zip input missing after clear: {input_files['repo']}")

        print(f"SetRecords result={result.get('result')}")
        print(f"after_backup={after_backup}")
        print(f"nonempty_after={sorted(after_nonempty)}")
        print(f"input_files={input_files}")
        print(f"errors={len(errors)}")
        for error in errors:
            print(f"ERROR: {error}")
        await browser.close()
        return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Clear Docker build result fields for the fresh task root.")
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    plan_path = args.plan or attachments.latest_plan_path()
    return asyncio.run(run(plan_path, apply=args.apply))


if __name__ == "__main__":
    raise SystemExit(main())
