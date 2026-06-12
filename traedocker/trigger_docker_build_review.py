#!/usr/bin/env python3
"""Set fresh root build status to pending review to trigger system build."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

import submit_new_task_attachments as attachments
import submit_new_task_group as group


PENDING_STATUS_OPTION = "optUcykA5z"  # 待质检


def empty_cell(cell_type: int) -> dict[str, Any]:
    return {"type": cell_type, "value": None}


def quality_ready_errors(payload: dict, root_id: str) -> list[str]:
    rows = group.summarize_records(payload)
    by_id = {row["recordId"]: row for row in rows}
    root = by_id.get(root_id)
    if not root:
        return [f"root record missing: {root_id}"]

    prompt_rows = [row for row in rows if row["parent"] == [root_id] and not row["session_id"]]
    prompt_ids = {row["recordId"] for row in prompt_rows}
    rollout_rows = [row for row in rows if row["parent"] and row["parent"][0] in prompt_ids and row["session_id"]]
    record_map = attachments.summarize_by_id(payload)
    errors: list[str] = []

    if group.base_value(record_map[root_id].get(group.FIELDS["submit_check"])) != group.OPT["submit_check"]["是"]:
        errors.append("submit_check is not marked 是")
    if len(prompt_rows) != 7:
        errors.append(f"prompt row count should be 7, got {len(prompt_rows)}")
    if len(rollout_rows) != 35:
        errors.append(f"rollout row count should be 35, got {len(rollout_rows)}")

    for row in prompt_rows + rollout_rows:
        rec = record_map.get(row["recordId"]) or {}
        prompt_check = group.unwrap_text(rec.get(group.FIELDS["prompt_check"])).strip()
        score_check = group.unwrap_text(rec.get(group.FIELDS["score_check"])).strip()
        if not prompt_check:
            errors.append(f"{row['recordId']} prompt_check is empty")
        if not score_check:
            errors.append(f"{row['recordId']} score_check is empty")
        if "不合理" in score_check:
            errors.append(f"{row['recordId']} score_check still says 不合理")

    return errors


async def run(plan_path: Path, apply: bool) -> int:
    plan = attachments.load_plan(plan_path)
    root_id = str(plan["root_id"])
    if root_id in group.PROTECTED_ROOT_IDS:
        raise RuntimeError("refusing to update old root record")

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
        before_backup = group.write_backup(before_payload, "before_trigger_docker_build_review")
        print(f"plan={plan_path}")
        print(f"root_id={root_id}")
        print(f"before_backup={before_backup}")
        ready_errors = quality_ready_errors(before_payload, root_id)
        print(f"quality_ready_errors={len(ready_errors)}")
        for error in ready_errors[:20]:
            print(f"ERROR: {error}")
        print("status_to_set=待质检")
        if ready_errors:
            await browser.close()
            return 1
        if not apply:
            print("dry run only; pass --apply to trigger")
            await browser.close()
            return 0

        updates = {
            group.FIELDS["docker_build_status"]: {"type": 3, "value": PENDING_STATUS_OPTION},
            group.FIELDS["docker_build_success"]: empty_cell(3),
            group.FIELDS["docker_build_retry_count"]: empty_cell(2),
            group.FIELDS["docker_build_log"]: empty_cell(17),
            group.FIELDS["docker_build_error"]: empty_cell(1),
            group.FIELDS["docker_build_at"]: empty_cell(1),
            group.FIELDS["docker_build_key"]: empty_cell(1),
            group.FIELDS["docker_build_screenshot"]: empty_cell(17),
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
        after_backup = group.write_backup(after_payload, "after_trigger_docker_build_review")
        rec = attachments.summarize_by_id(after_payload).get(root_id) or {}
        status = rec.get(group.FIELDS["docker_build_status"])
        raw_status = status.get("value") if isinstance(status, dict) else status
        print(f"SetRecords result={result.get('result')}")
        print(f"after_backup={after_backup}")
        print(f"status_value={raw_status}")
        print(f"input_files={{'dockerfile': {attachments.cell_files(rec, 'dockerfile')}, 'repo': {attachments.cell_files(rec, 'repo')}}}")
        await browser.close()
        return 0 if raw_status == PENDING_STATUS_OPTION else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Trigger system Docker build by setting pending review status.")
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    plan_path = args.plan or attachments.latest_plan_path()
    return asyncio.run(run(plan_path, apply=args.apply))


if __name__ == "__main__":
    raise SystemExit(main())
