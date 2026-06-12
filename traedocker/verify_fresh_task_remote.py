#!/usr/bin/env python3
"""Full remote verification for the latest fresh Bitable task group."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

import submit_new_task_attachments as attachments
import submit_new_task_group as group


def _select_token(record: dict, field_key: str) -> str:
    cell = record.get(group.FIELDS[field_key])
    if not cell:
        return ""
    raw = cell.get("value") if isinstance(cell, dict) else cell
    return str(raw or "")


def validate_build_metadata(record_map: dict[str, dict], root_id: str) -> list[str]:
    root = record_map.get(root_id)
    if not root:
        return [f"fresh root record missing for build metadata: {root_id}"]

    errors: list[str] = []
    status = _select_token(root, "docker_build_status")
    success = _select_token(root, "docker_build_success")
    retry_count = root.get(group.FIELDS["docker_build_retry_count"])
    retry_value = retry_count.get("value") if isinstance(retry_count, dict) else retry_count
    log_files = attachments.cell_files(root, "docker_build_log")
    error_text = group.unwrap_text(root.get(group.FIELDS["docker_build_error"])).strip()
    built_at = group.unwrap_text(root.get(group.FIELDS["docker_build_at"])).strip()
    build_key = group.unwrap_text(root.get(group.FIELDS["docker_build_key"])).strip()

    if success != group.OPT["docker_build_success"]["true"]:
        errors.append("docker_build_success is not true")
    if status != group.OPT["docker_build_status"]["成功"]:
        errors.append("docker_build_status is not 成功")
    if retry_value != 0:
        errors.append(f"docker_build_retry_count should be 0, got {retry_value}")
    if not log_files:
        errors.append("docker_build_log attachment is missing")
    if not error_text:
        errors.append("docker_build_error summary is missing")
    if not built_at:
        errors.append("docker_build_at is missing")
    if not build_key:
        errors.append("docker_build_key is missing")
    return errors


async def main_async(plan_path: Path, artifact_dir: Path | None = None) -> int:
    artifact_dir = (artifact_dir or attachments.infer_artifact_dir(plan_path)).resolve()
    plan = attachments.load_plan(plan_path)
    trial_rows = attachments.load_trial_rows(artifact_dir)

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
        payload = await attachments.fetch_payload(page)
        backup = group.write_backup(payload, "full_remote_recheck")
        errors = attachments.validate_shapes_and_attachments(payload, plan, trial_rows, require_attachments=True)

        rows = group.summarize_records(payload)
        by_id = {row["recordId"]: row for row in rows}
        root_id = str(plan["root_id"])
        prompt_ids = set(str(value) for value in plan["prompt_ids"].values())
        rollout_ids = set(str(value) for value in plan["rollout_ids"].values())
        new_prompts = {row["recordId"] for row in rows if row["parent"] == [root_id] and not row["session_id"]}
        new_rollouts = {row["recordId"] for row in rows if row["parent"] and row["parent"][0] in prompt_ids and row["session_id"]}
        local_sessions = {row["session_id"] for row in trial_rows}
        current_session_records = {
            row["recordId"]
            for row in rows
            if any(group.session_value_matches(row["session_id"], session_id) for session_id in local_sessions)
        }

        if new_prompts != prompt_ids:
            errors.append("new prompt record set does not match the plan")
        if new_rollouts != rollout_ids:
            errors.append("new rollout record set does not match the plan")
        if current_session_records != rollout_ids:
            errors.append("current-run sessions are not exactly in the fresh group rollout records")

        record_map = attachments.summarize_by_id(payload)
        errors.extend(validate_build_metadata(record_map, root_id))
        root_files = {
            "dockerfile": attachments.cell_files(record_map[root_id], "dockerfile"),
            "repo": attachments.cell_files(record_map[root_id], "repo"),
            "docker_build_screenshot": attachments.cell_files(record_map[root_id], "docker_build_screenshot"),
            "docker_build_log": attachments.cell_files(record_map[root_id], "docker_build_log"),
        }

        print(f"backup={backup}")
        print(f"plan={plan_path}")
        print(f"artifact_dir={artifact_dir}")
        print(f"total_rows={len(rows)}")
        print(f"fresh_root={root_id} {by_id.get(root_id, {}).get('primary')} prompts={len(new_prompts)} rollouts={len(new_rollouts)}")
        print(f"fresh_root_files={root_files}")
        print(f"errors={len(errors)}")
        for error in errors[:80]:
            print(f"ERROR: {error}")
        await browser.close()
        return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Full remote verification for a fresh Bitable task group.")
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--artifact-dir", type=Path)
    args = parser.parse_args()
    plan_path = args.plan or attachments.latest_plan_path()
    return asyncio.run(main_async(plan_path, artifact_dir=args.artifact_dir))


if __name__ == "__main__":
    raise SystemExit(main())
