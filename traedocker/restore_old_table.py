#!/usr/bin/env python3
"""Restore the old Bitable by deleting only this run's accidentally written rows.

Default mode is dry-run. Use --apply to execute DeleteRecords after the script
has backed up the server state and printed the exact record IDs to delete.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

import submit_missing_rollouts as submit


BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / "restore_backups"


def load_trial_session_ids() -> set[str]:
    session_ids: set[str] = set()
    with (BASE_DIR / "trial_log.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            session_id = (row.get("session_id") or "").strip()
            if session_id:
                session_ids.add(session_id)
    if len(session_ids) != 35:
        raise RuntimeError(f"expected 35 local trial session IDs, got {len(session_ids)}")
    return session_ids


async def fetch_backup_payload(page) -> dict[str, Any]:
    return await page.evaluate(
        """
        async ({ token, table, view }) => {
          const tableObj = window.bitableStore.modelOperator.getTableById(table);
          const rev = tableObj.rev;
          const url = `/space/api/v1/bitable/${token}/records?tableId=${table}&viewId=${view}&tableRev=${rev}&depRev=%7B%7D&viewLazyLoad=true&offset=0&limit=3000&tableID=${table}&viewID=${view}&removeFmlExtra=true`;
          const json = await (await fetch(url, { credentials: 'include' })).json();
          const decoded = await window.unGzipBase64(json.data.records);
          return {
            fetchedAt: new Date().toISOString(),
            pageUrl: location.href,
            tableRev: rev,
            raw: JSON.parse(decoded),
          };
        }
        """,
        {"token": submit.BASE_TOKEN, "table": submit.TABLE_ID, "view": submit.VIEW_ID},
    )


def write_backup(payload: dict[str, Any], label: str) -> Path:
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = BACKUP_DIR / f"{label}_{stamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_delete_plan(rows: list[dict[str, Any]], session_ids: set[str]) -> list[dict[str, Any]]:
    targets = []
    for row in rows:
        session_id = row.get("session_id") or ""
        if session_id in session_ids:
            targets.append(row)
    return sorted(targets, key=lambda row: (row.get("prompt_index") or "", row.get("rollout_id") or "", row["recordId"]))


async def delete_records(page, record_ids: list[str]) -> dict[str, Any]:
    return await page.evaluate(
        """
        ({ table, view, recordIds }) => {
          const result = window.bitableStore.commandManager.execute({
            cmd: 'DeleteRecords',
            tableId: table,
            viewId: view,
            recordIds,
          });
          return JSON.parse(JSON.stringify(result, (key, value) => {
            if (typeof value === 'function') return '[function]';
            return value;
          }));
        }
        """,
        {"table": submit.TABLE_ID, "view": submit.VIEW_ID, "recordIds": record_ids},
    )


async def run(apply: bool) -> int:
    session_ids = load_trial_session_ids()
    rollouts = submit.load_rollouts()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:9235")
        pages = [page for ctx in browser.contexts for page in ctx.pages if submit.BASE_TOKEN in page.url]
        if not pages:
            await browser.close()
            raise RuntimeError("old Bitable page is not open in the logged-in browser")
        page = pages[0]
        await page.bring_to_front()
        await submit.reset_page(page)

        before_payload = await fetch_backup_payload(page)
        before_path = write_backup(before_payload, "old_table_before_restore")
        missing, wrong_git, wrong_fields, rows = await submit.get_missing(page, rollouts)
        targets = build_delete_plan(rows, session_ids)
        plan_path = write_backup({"targets": targets}, "old_table_restore_delete_plan")

        print(f"Backup: {before_path}")
        print(f"Delete plan: {plan_path}")
        print(
            f"Before restore: rows={len(rows)} local-session rows={len(targets)} "
            f"missing={len(missing)} wrong_git={len(wrong_git)} wrong_fields={len(wrong_fields)}"
        )
        for row in targets:
            print(
                "  target: "
                f"{row['recordId']} P{row.get('prompt_index')} R{row.get('rollout_id')} "
                f"{row.get('model_name')} {row.get('session_id')}"
            )

        if not targets:
            print("No accidental current-run rows found. Nothing to restore.")
            await browser.close()
            return 0

        if not apply:
            print("Dry-run only. Re-run with --apply to delete exactly these target rows.")
            await browser.close()
            return 2

        result = await delete_records(page, [row["recordId"] for row in targets])
        print(
            f"DeleteRecords result={result.get('result')} "
            f"redo_actions={len(result.get('actions', {}).get('redo', []))}"
        )
        if result.get("result") != 0:
            await browser.close()
            raise RuntimeError(f"DeleteRecords failed: {result}")

        await asyncio.sleep(8)
        await page.reload(wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_function(
            "({ table }) => !!window.bitableStore?.modelOperator?.getTableById(table)",
            arg={"table": submit.TABLE_ID},
            timeout=30000,
        )
        await asyncio.sleep(3)

        after_payload = await fetch_backup_payload(page)
        after_path = write_backup(after_payload, "old_table_after_restore")
        after_missing, after_wrong_git, after_wrong_fields, after_rows = await submit.get_missing(page, rollouts)
        remaining = build_delete_plan(after_rows, session_ids)

        print(f"After backup: {after_path}")
        print(
            f"After restore: rows={len(after_rows)} local-session rows={len(remaining)} "
            f"missing={len(after_missing)} wrong_git={len(after_wrong_git)} "
            f"wrong_fields={len(after_wrong_fields)}"
        )
        for row in remaining:
            print(f"  still present: {row['recordId']} {row.get('session_id')}")

        await browser.close()
        return 1 if remaining else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore old Bitable by deleting current-run accidental rows.")
    parser.add_argument("--apply", action="store_true", help="Actually delete the planned current-run rows.")
    args = parser.parse_args()
    return asyncio.run(run(apply=args.apply))


if __name__ == "__main__":
    raise SystemExit(main())
