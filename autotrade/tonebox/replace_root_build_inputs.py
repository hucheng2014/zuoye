#!/usr/bin/env python3
"""Replace Dockerfile and repo.zip inputs on a fresh task root."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

import submit_new_task_attachments as attachments
import submit_new_task_group as group


INPUT_SPECS = [
    ("dockerfile", "dockerfile", "Dockerfile"),
    ("repo", "repo", "repo.zip"),
]


async def run(plan_path: Path, artifact_dir: Path, apply: bool) -> int:
    plan = attachments.load_plan(plan_path)
    root_id = str(plan["root_id"])
    if root_id == group.OLD_ROOT_RECORD_ID:
        raise RuntimeError("refusing to replace inputs on old root record")

    targets = [
        attachments.AttachmentTarget(root_id, field_key, field_label, artifact_dir / file_name)
        for field_key, field_label, file_name in INPUT_SPECS
    ]
    for target in targets:
        if not target.file_path.exists():
            raise FileNotFoundError(target.file_path)

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
        before_backup = group.write_backup(before_payload, "before_replace_root_build_inputs")
        before_root = attachments.summarize_by_id(before_payload).get(root_id) or {}
        print(f"plan={plan_path}")
        print(f"artifact_dir={artifact_dir}")
        print(f"root_id={root_id}")
        print(f"before_backup={before_backup}")
        for target in targets:
            print(f"before_{target.field_key}={attachments.cell_files(before_root, target.field_key)}")
        if not apply:
            print("dry run only; pass --apply to replace inputs")
            await browser.close()
            return 0

        for target in targets:
            upload = await attachments.upload_drive_file(page, target.file_path)
            cell = attachments.attachment_cell(upload, target.file_path)
            result = await attachments.set_attachment_cell(page, target, cell)
            print(
                f"replaced {target.field_key}: file={target.file_name} "
                f"token={upload['token']} result={result.get('result')}"
            )
            await attachments.wait_for_server_file(page, target)

        after_payload = await attachments.fetch_payload(page)
        after_backup = group.write_backup(after_payload, "after_replace_root_build_inputs")
        after_root = attachments.summarize_by_id(after_payload).get(root_id) or {}
        errors: list[str] = []
        for target in targets:
            names = attachments.cell_files(after_root, target.field_key)
            if names != [target.file_name]:
                errors.append(f"{target.field_key} expected only {target.file_name}, got {names}")
            print(f"after_{target.field_key}={names}")

        print(f"after_backup={after_backup}")
        print(f"errors={len(errors)}")
        for error in errors:
            print(f"ERROR: {error}")
        await browser.close()
        return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Replace root Dockerfile and repo.zip attachments.")
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    plan_path = args.plan or attachments.latest_plan_path()
    artifact_dir = (args.artifact_dir or attachments.infer_artifact_dir(plan_path)).resolve()
    return asyncio.run(run(plan_path, artifact_dir, apply=args.apply))


if __name__ == "__main__":
    raise SystemExit(main())
