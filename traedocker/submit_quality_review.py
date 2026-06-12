#!/usr/bin/env python3
"""Mark an existing fresh task group ready for project QA review."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

import submit_new_task_attachments as attachments
import submit_new_task_group as group
from bitable_score_reason import find_latest_plan, load_plan, normalize_trial_log
from submit_new_task_group import (
    FIELDS,
    Rollout,
    load_prompts,
    score_quality_text,
    select_cell,
    text_cell,
)


async def fetch_rows(page) -> list[dict[str, Any]]:
    return await page.evaluate(
        """
        async ({ token, table, view, fields }) => {
          const tableObj = window.bitableStore.modelOperator.getTableById(table);
          const getField = (id) => tableObj.fields?.[id] || tableObj.fieldsMap?.get?.(id);
          const optionNames = {};
          for (const name of ['submit_check', 'task_status']) {
            const field = getField(fields[name]);
            optionNames[name] = Object.fromEntries((field?.property?.options || []).map(opt => [opt.id, opt.name]));
          }
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
          const unwrapSelect = (name, cell) => {
            const value = baseValue(cell);
            if (value == null) return '';
            if (typeof value === 'string') return optionNames[name]?.[value] ?? value;
            return '';
          };
          const parentId = (cell) => {
            const value = baseValue(cell);
            if (!Array.isArray(value) || !value.length) return '';
            const first = value[0];
            if (typeof first === 'string') return first;
            return first?.recordIds?.[0] ?? first?.id ?? '';
          };
          return Object.entries(parsed.recordMap || {}).map(([recordId, rec]) => ({
            recordId,
            parent_id: parentId(rec[fields.parent]),
            prompt_index: unwrapText(rec[fields.prompt_index]),
            session_id: unwrapText(rec[fields.session_id]),
            submit_check: unwrapSelect('submit_check', rec[fields.submit_check]),
            task_status: unwrapSelect('task_status', rec[fields.task_status]),
            prompt_check: unwrapText(rec[fields.prompt_check]),
            score_check: unwrapText(rec[fields.score_check]),
          }));
        }
        """,
        {
            "token": group.BASE_TOKEN,
            "table": group.TABLE_ID,
            "view": group.VIEW_ID,
            "fields": FIELDS,
        },
    )


PROMPT_SCORE_CHECK_TEXT = "prompt 级记录，无 rollout 评分；已完成 prompt 质量复核。"


async def set_records(page, updates: dict[str, dict[str, Any]]) -> dict[str, Any]:
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
        {"table": group.TABLE_ID, "view": group.VIEW_ID, "updates": updates},
    )


def rollout_by_session() -> tuple[dict[str, Rollout], dict[int, str]]:
    from submit_new_task_group import MODEL_OPTION_TEXT, MODEL_ROLLOUT_ID

    normalize_trial_log()
    prompts = load_prompts()
    by_session: dict[str, Rollout] = {}
    import csv

    with (group.BASE_DIR / "trial_log.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            from bitable_score_reason import build_score_reason

            session_id = row["session_id"].strip()
            prompt = int(row["prompt"])
            reason = build_score_reason(
                prompt,
                row["model"],
                row["score"].strip(),
                row["patch_file"],
                row["score_reason"].strip(),
            )
            by_session[session_id] = Rollout(
                prompt=prompt,
                model=row["model"],
                session_id=session_id,
                score=row["score"].strip(),
                score_reason=reason,
                patch_file=group.BASE_DIR / row["patch_file"],
                rollout_id=MODEL_ROLLOUT_ID[row["model"]],
                model_option=MODEL_OPTION_TEXT[row["model"]],
            )
    return by_session, prompts


async def run(plan_path: Path, apply: bool) -> int:
    root_id, session_to_record, rollout_record_ids, prompt_record_ids = load_plan(plan_path)
    if root_id in group.PROTECTED_ROOT_IDS:
        raise RuntimeError(f"refusing to submit QA on protected root {root_id}")

    rollouts_by_session, prompts = rollout_by_session()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp(attachments.CDP_URL)
        pages = [page for ctx in browser.contexts for page in ctx.pages if group.BASE_TOKEN in page.url]
        if not pages:
            await browser.close()
            raise RuntimeError("Bitable page is not open in traedocker browser")
        page = pages[0]
        await page.bring_to_front()
        await page.wait_for_function(
            "({ table }) => !!window.bitableStore?.modelOperator?.getTableById(table)",
            arg={"table": group.TABLE_ID},
            timeout=30000,
        )

        before = await fetch_rows(page)
        group.write_backup({"rows": before, "plan": str(plan_path)}, f"before_submit_quality_{stamp}")

        by_id = {row["recordId"]: row for row in before}
        prompt_updates: dict[str, dict[str, Any]] = {}
        rollout_updates: dict[str, dict[str, Any]] = {}
        root_submit_update: dict[str, dict[str, Any]] = {}
        root_status_update: dict[str, dict[str, Any]] = {}

        root = by_id.get(root_id)
        if not root:
            raise RuntimeError(f"root record missing: {root_id}")
        if root.get("submit_check") != "是":
            root_submit_update[root_id] = {
                FIELDS["submit_check"]: select_cell("submit_check", "是"),
            }
        if root.get("task_status") != "待验收（已内部质检）":
            root_status_update[root_id] = {
                FIELDS["task_status"]: select_cell("task_status", "待验收（已内部质检）"),
            }

        for prompt_id in sorted(prompt_record_ids):
            row = by_id.get(prompt_id)
            if not row:
                raise RuntimeError(f"prompt record missing: {prompt_id}")
            prompt_index = int(row.get("prompt_index") or "0")
            if not prompt_index:
                raise RuntimeError(f"prompt_index missing for {prompt_id}")
            fields: dict[str, Any] = {}
            if row.get("score_check") != PROMPT_SCORE_CHECK_TEXT:
                fields[FIELDS["score_check"]] = text_cell(PROMPT_SCORE_CHECK_TEXT)
            if fields:
                prompt_updates[prompt_id] = fields

        plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
        for key, record_id in plan_data["rollout_ids"].items():
            session_id = key.rsplit("|", 1)[-1]
            row = None
            for candidate in before:
                if candidate["recordId"] == record_id:
                    row = candidate
                    break
                remote_sid = candidate.get("session_id") or ""
                if group.session_value_matches(remote_sid, session_id):
                    row = candidate
                    break
            if not row:
                raise RuntimeError(f"rollout row missing for {session_id}")
            rollout = rollouts_by_session[session_id]
            prompt_text = prompts[rollout.prompt]
            fields = {}
            expected_score_check = score_quality_text(prompt_text, rollout)
            if "不合理" in (row.get("score_check") or "") or row.get("score_check") != expected_score_check:
                fields[FIELDS["score_check"]] = text_cell(expected_score_check)
            if fields:
                rollout_updates[record_id] = fields

        unreasonable = [
            row["recordId"]
            for row in before
            if row["recordId"] in (rollout_record_ids | prompt_record_ids)
            and "不合理" in (row.get("score_check") or "")
        ]
        print(f"plan={plan_path}")
        print(f"root_id={root_id}")
        print(
            "updates="
            f"{len(prompt_updates) + len(rollout_updates) + int(bool(root_submit_update)) + int(bool(root_status_update))} "
            f"prompts={len(prompt_updates)} rollouts={len(rollout_updates)} "
            f"unreasonable_rows={len(unreasonable)} apply={apply}"
        )
        if unreasonable:
            print("ERROR: score_check still unreasonable on:", unreasonable[:5])
            await browser.close()
            return 1

        async def apply_batches(updates: dict[str, dict[str, Any]], label: str, batch_size: int = 8) -> None:
            if not apply or not updates:
                return
            items = list(updates.items())
            for batch_start in range(0, len(items), batch_size):
                batch = dict(items[batch_start : batch_start + batch_size])
                result = await set_records(page, batch)
                print(
                    f"{label} batch {batch_start // batch_size + 1}: "
                    f"result={result.get('result')} records={len(batch)}"
                )
                if result.get("result") != 2:
                    raise RuntimeError(f"SetRecords failed ({label}): {result}")
                await page.wait_for_timeout(2000)

        await apply_batches(prompt_updates, "prompt", batch_size=3)
        await apply_batches(rollout_updates, "rollout", batch_size=8)
        if apply and root_submit_update:
            result = await set_records(page, root_submit_update)
            print(f"root submit_check: result={result.get('result')}")
            if result.get("result") != 2:
                await browser.close()
                raise RuntimeError(f"SetRecords failed (root submit_check): {result}")
            await page.wait_for_timeout(2000)
        if apply and root_status_update:
            result = await set_records(page, root_status_update)
            print(f"root task_status: result={result.get('result')} reason={result.get('reason')}")
            if result.get("result") != 2:
                print(
                    "WARN: task_status could not be set automatically; "
                    "submit_check may still be enough. Set 题目状态 manually if required."
                )
            await page.wait_for_timeout(2000)

        after = await fetch_rows(page)
        group.write_backup({"rows": after, "plan": str(plan_path)}, f"after_submit_quality_{stamp}")
        root_after = next(row for row in after if row["recordId"] == root_id)
        print(f"submit_check={root_after.get('submit_check')}")
        print(f"task_status={root_after.get('task_status')}")
        await browser.close()
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Submit fresh task group for project QA review.")
    parser.add_argument("--plan", type=Path, default=None)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    plan_path = args.plan or find_latest_plan()
    return asyncio.run(run(plan_path.resolve(), apply=args.apply))


if __name__ == "__main__":
    raise SystemExit(main())
