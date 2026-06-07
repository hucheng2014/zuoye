#!/usr/bin/env python3
"""Upload and verify attachments for the current fresh Bitable task group.

This script is deliberately scoped to the record IDs saved in a
new_task_group_plan_*.json file. It never creates records and never targets the
old task root.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

import submit_new_task_group as group


BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / "new_task_backups"
CDP_URL = "http://127.0.0.1:9235"
OLD_ROOT_RECORD_ID = group.OLD_ROOT_RECORD_ID

ROOT_ATTACHMENT_SPECS = [
    ("dockerfile", "dockerfile", "Dockerfile"),
    ("repo", "repo", "repo.zip"),
    ("docker_build_screenshot", "dockerfile构建成功截图", "docker_build_success.png"),
]


@dataclass(frozen=True)
class AttachmentTarget:
    record_id: str
    field_key: str
    field_label: str
    file_path: Path

    @property
    def file_name(self) -> str:
        return self.file_path.name


def latest_plan_path() -> Path:
    plans = sorted(BACKUP_DIR.glob("new_task_group_plan_*.json"))
    if not plans:
        raise RuntimeError("no new_task_group_plan_*.json found")
    return plans[-1]


def infer_artifact_dir(plan_path: Path) -> Path:
    if plan_path.parent.name == "new_task_backups":
        return plan_path.parent.parent
    return BASE_DIR


def load_plan(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {"root_id", "prompt_ids", "rollout_ids", "record_count"}
    missing = required.difference(payload)
    if missing:
        raise RuntimeError(f"plan missing keys: {sorted(missing)}")
    if payload["root_id"] == OLD_ROOT_RECORD_ID:
        raise RuntimeError("refusing to target the old root record")
    if int(payload["record_count"]) != 43:
        raise RuntimeError(f"expected 43 records in plan, got {payload['record_count']}")
    return payload


def load_trial_rows(artifact_dir: Path = BASE_DIR) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with (artifact_dir / "trial_log.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(row)
    if len(rows) != 35:
        raise RuntimeError(f"expected 35 rollout rows in trial_log.csv, got {len(rows)}")
    return rows


def build_targets(plan: dict[str, Any], trial_rows: list[dict[str, str]], artifact_dir: Path = BASE_DIR) -> list[AttachmentTarget]:
    targets: list[AttachmentTarget] = []
    root_id = str(plan["root_id"])
    for field_key, field_label, file_name in ROOT_ATTACHMENT_SPECS:
        targets.append(AttachmentTarget(root_id, field_key, field_label, artifact_dir / file_name))

    rollout_ids = plan["rollout_ids"]
    for row in trial_rows:
        key = f"P{row['prompt']}|{row['model']}|{row['session_id']}"
        record_id = rollout_ids.get(key)
        if not record_id:
            raise RuntimeError(f"plan has no rollout record for {key}")
        patch_path = artifact_dir / row["patch_file"]
        targets.append(AttachmentTarget(record_id, "git_diff", "git_diff", patch_path))

    for target in targets:
        if not target.file_path.exists():
            raise FileNotFoundError(target.file_path)
    return targets


def unwrap_text(cell: Any) -> str:
    return group.unwrap_text(cell)


def cell_files(record: dict[str, Any], field_key: str) -> list[str]:
    return group.file_names(record.get(group.FIELDS[field_key]))


def summarize_by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return payload["raw"].get("recordMap") or {}


def primary_number(record: dict[str, Any]) -> str:
    value = record.get(group.FIELDS["primary"])
    if not value:
        return ""
    raw = value.get("value") if isinstance(value, dict) else value
    if isinstance(raw, list) and raw and isinstance(raw[0], dict):
        return str(raw[0].get("number") or "")
    return ""


def parent_value(record: dict[str, Any]) -> list[str]:
    value = record.get(group.FIELDS["parent"])
    if not value:
        return []
    raw = value.get("value") if isinstance(value, dict) else value
    return raw if isinstance(raw, list) else []


def record_session(record: dict[str, Any]) -> str:
    return unwrap_text(record.get(group.FIELDS["session_id"]))


def validate_shapes_and_attachments(
    payload: dict[str, Any],
    plan: dict[str, Any],
    trial_rows: list[dict[str, str]],
    *,
    require_attachments: bool,
) -> list[str]:
    errors: list[str] = []
    record_map = summarize_by_id(payload)
    rows = group.summarize_records(payload)
    by_id = {row["recordId"]: row for row in rows}

    root_id = str(plan["root_id"])
    prompt_ids = {int(k): str(v) for k, v in plan["prompt_ids"].items()}
    rollout_record_ids = set(str(v) for v in plan["rollout_ids"].values())
    local_sessions = {row["session_id"] for row in trial_rows}

    if len(rows) != 86:
        errors.append(f"table row count should be 86 after old+new groups, got {len(rows)}")

    if root_id == OLD_ROOT_RECORD_ID:
        errors.append("new plan points at old root")
    if OLD_ROOT_RECORD_ID not in by_id:
        errors.append(f"old root missing: {OLD_ROOT_RECORD_ID}")
    if root_id not in by_id:
        errors.append(f"new root missing: {root_id}")

    old_prompt_ids = {
        row["recordId"]
        for row in rows
        if row["parent"] == [OLD_ROOT_RECORD_ID] and not row["session_id"]
    }
    old_rollouts = [
        row
        for row in rows
        if row["parent"] and row["parent"][0] in old_prompt_ids and row["session_id"]
    ]
    if len(old_prompt_ids) != 7 or len(old_rollouts) != 35:
        errors.append(f"old group shape mismatch: prompts={len(old_prompt_ids)} rollouts={len(old_rollouts)}")

    current_session_rows = [row for row in rows if row["session_id"] in local_sessions]
    current_session_ids = {row["recordId"] for row in current_session_rows}
    if current_session_ids != rollout_record_ids:
        errors.append(
            "current-run sessions are not exactly under the new rollout records: "
            f"expected={len(rollout_record_ids)} actual={len(current_session_ids)} "
            f"extra={sorted(current_session_ids - rollout_record_ids)[:5]} "
            f"missing={sorted(rollout_record_ids - current_session_ids)[:5]}"
        )

    for prompt_index, prompt_id in prompt_ids.items():
        prompt_row = by_id.get(prompt_id)
        if not prompt_row:
            errors.append(f"P{prompt_index} prompt record missing: {prompt_id}")
        elif prompt_row["parent"] != [root_id]:
            errors.append(f"P{prompt_index} prompt parent mismatch: {prompt_row['parent']} != {[root_id]}")

    for row in trial_rows:
        key = f"P{row['prompt']}|{row['model']}|{row['session_id']}"
        rid = str(plan["rollout_ids"].get(key) or "")
        rec_summary = by_id.get(rid)
        expected_parent = prompt_ids[int(row["prompt"])]
        if not rec_summary:
            errors.append(f"rollout record missing for {key}: {rid}")
            continue
        if rec_summary["parent"] != [expected_parent]:
            errors.append(f"rollout parent mismatch for {key}: {rec_summary['parent']} != {[expected_parent]}")
        if rec_summary["session_id"] != row["session_id"]:
            errors.append(f"rollout session mismatch for {key}: {rec_summary['session_id']}")

    if require_attachments and root_id in record_map:
        root = record_map[root_id]
        for field_key, _label, file_name in ROOT_ATTACHMENT_SPECS:
            names = cell_files(root, field_key)
            if file_name not in names:
                errors.append(f"root {field_key} missing {file_name}; has={names}")

    if require_attachments:
        for row in trial_rows:
            key = f"P{row['prompt']}|{row['model']}|{row['session_id']}"
            rid = str(plan["rollout_ids"].get(key) or "")
            rec = record_map.get(rid)
            expected = Path(row["patch_file"]).name
            names = cell_files(rec or {}, "git_diff")
            if expected not in names:
                errors.append(f"rollout git_diff missing for {key}: expected {expected}; has={names}")

    return errors


async def close_overlays(page) -> None:
    for _ in range(3):
        await page.keyboard.press("Escape")
        await asyncio.sleep(0.25)
    for text in ["Back to Edit", "返回编辑"]:
        button = page.locator(f"button:visible:has-text('{text}')").first
        if await button.count():
            await button.click(force=True)
            await asyncio.sleep(1.0)


async def fetch_payload(page) -> dict[str, Any]:
    return await group.fetch_payload(page)


async def open_record(page, record_id: str, expected_bnum: str) -> None:
    url = (
        f"https://bytedance.larkoffice.com/base/{group.BASE_TOKEN}"
        f"?table={group.TABLE_ID}&view={group.VIEW_ID}&record={record_id}"
    )
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_function(
        "({ table }) => !!window.bitableStore?.modelOperator?.getTableById(table)",
        arg={"table": group.TABLE_ID},
        timeout=30000,
    )
    await page.wait_for_function(
        """
        ({ expected }) => {
          const visible = (el) => {
            const r = el.getBoundingClientRect();
            const st = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && st.visibility !== 'hidden' && st.display !== 'none';
          };
          const drawers = Array.from(document.querySelectorAll(
            '.bitable-drawer-card, .ud__drawer-open, .bitable-record-card-content, .base-record-card, [class*="record-card"]'
          )).filter(visible);
          return drawers.some((el) => (el.innerText || '').includes(expected));
        }
        """,
        arg={"expected": expected_bnum},
        timeout=30000,
    )
    await asyncio.sleep(0.8)


async def reset_record_scroll(page) -> None:
    await page.evaluate(
        """
        () => {
          const selectors = [
            '.ud__scrollArea-y',
            '.bitable-record-card-content',
            '.bitable-drawer-card-content',
            '.base-record-card',
            '[class*="record-card"]',
            '[class*="drawer"]'
          ];
          for (const el of document.querySelectorAll(selectors.join(','))) {
            if (el.scrollHeight > el.clientHeight) el.scrollTop = 0;
          }
        }
        """
    )
    await asyncio.sleep(0.25)


async def get_field_row(page, field_label: str):
    selectors = ", ".join(
        [
            ".base_record_card_field_editor_wrapper",
            ".bitable-node-container-wrapper-field",
            ".bitable-record-card-field-wrapper",
            ".bitable-field-item",
            "[class*='field-editor-wrapper']",
            "[class*='field-wrapper']",
        ]
    )
    for _ in range(18):
        count = await page.locator(selectors).count()
        for index in range(count):
            row = page.locator(selectors).nth(index)
            label = row.locator(".bitable-field-name, [class*='field-name'], [class*='field-label']").first
            if not await label.count():
                continue
            raw = (await label.inner_text()).replace("\u200b", "").strip().split("\n")[0]
            if raw == field_label:
                await row.evaluate("el => el.scrollIntoView({ block: 'center', inline: 'nearest' })")
                try:
                    await row.scroll_into_view_if_needed(timeout=4000)
                except PlaywrightTimeoutError:
                    pass
                await asyncio.sleep(0.4)
                return row
        await page.evaluate(
            """
            () => {
              const selectors = [
                '.ud__scrollArea-y',
                '.bitable-record-card-content',
                '.bitable-drawer-card-content',
                '.base-record-card',
                '[class*="record-card"]',
                '[class*="drawer"]'
              ];
              for (const el of document.querySelectorAll(selectors.join(','))) {
                if (el.scrollHeight > el.clientHeight) {
                  el.scrollBy(0, 420);
                  return;
                }
              }
            }
            """
        )
        await asyncio.sleep(0.35)
    return None


async def upload_attachment(page, target: AttachmentTarget) -> None:
    await reset_record_scroll(page)
    row = await get_field_row(page, target.field_label)
    if not row:
        raise RuntimeError(f"field not found: {target.field_label} on {target.record_id}")

    for attempt in range(3):
        click_box = await row.evaluate(
            """
            (el) => {
              const visible = (node) => {
                const r = node.getBoundingClientRect();
                const st = getComputedStyle(node);
                return r.width > 0 && r.height > 0 && st.visibility !== 'hidden' && st.display !== 'none';
              };
              const selectors = [
                '.b-collapsed-attach-editor__btn',
                '[class*="add-attach"]',
                '[class*="upload"]',
                '[class*="Attachment"]',
                'button'
              ];
              const candidates = Array.from(el.querySelectorAll(selectors.join(','))).filter(visible);
              const target = candidates.find((node) => /add attachment|上传|添加/i.test(node.innerText || ''))
                || candidates[0];
              if (!target) return null;
              target.scrollIntoView({ block: 'center', inline: 'nearest' });
              const r = target.getBoundingClientRect();
              return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
            }
            """
        )
        if not click_box:
            if attempt == 2:
                raise RuntimeError(f"attachment button not found for {target.field_label}")
            await asyncio.sleep(0.5)
            continue

        try:
            async with page.expect_file_chooser(timeout=8000) as chooser_info:
                await page.mouse.click(click_box["x"], click_box["y"])
            chooser = await chooser_info.value
            await chooser.set_files(str(target.file_path))
        except PlaywrightTimeoutError:
            file_input = page.locator("input#attachment-upload, input[type='file']").last
            if await file_input.count() == 0:
                if attempt == 2:
                    raise RuntimeError("attachment file input did not appear")
                continue
            await file_input.set_input_files(str(target.file_path), timeout=10000)

        await page.wait_for_function(
            "(name) => document.body.innerText.includes(name)",
            arg=target.file_name,
            timeout=45000,
        )
        await asyncio.sleep(2.0)
        return

    raise RuntimeError(f"upload failed: {target.file_name}")


def target_missing(record_map: dict[str, dict[str, Any]], target: AttachmentTarget) -> bool:
    rec = record_map.get(target.record_id)
    if not rec:
        raise RuntimeError(f"record missing: {target.record_id}")
    return target.file_name not in cell_files(rec, target.field_key)


async def upload_drive_file(page, file_path: Path) -> dict[str, Any]:
    input_handle = await page.evaluate_handle(
        """
        () => {
          let input = document.querySelector('#codex-new-task-drive-upload');
          if (!input) {
            input = document.createElement('input');
            input.type = 'file';
            input.id = 'codex-new-task-drive-upload';
            input.style.position = 'fixed';
            input.style.left = '-10000px';
            input.style.top = '0';
            document.body.appendChild(input);
          }
          input.value = '';
          return input;
        }
        """
    )
    element = input_handle.as_element()
    if not element:
        raise RuntimeError("failed to create upload input")
    await element.set_input_files(str(file_path))
    result = await page.evaluate(
        """
        async ({ table }) => {
          const input = document.querySelector('#codex-new-task-drive-upload');
          const file = input?.files?.[0];
          if (!file) throw new Error('upload input has no file');

          let dimensions = {};
          if ((file.type || '').startsWith('image/') && window.createImageBitmap) {
            try {
              const bitmap = await createImageBitmap(file);
              dimensions = { width: bitmap.width, height: bitmap.height };
              bitmap.close?.();
            } catch (_err) {}
          }

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
          const events = [];
          for (const name of ['tasks_added', 'tasks_changed', 'parse_error', 'runtime_incident_occurred']) {
            uploader.on(name, (payload) => {
              events.push(JSON.parse(JSON.stringify({ event: name, payload }, (key, value) => {
                if (value instanceof File) return { name: value.name, size: value.size, type: value.type };
                if (typeof value === 'function') return '[function]';
                return value;
              })));
            });
          }

          const opts = {
            jobType: 1,
            parentToken: window.bitableStore.token,
            mountPoint: 'bitable',
            businessType: 1,
            shouldAddToRecents: false,
            sizeLimit: 1024 * 1024 * 1024,
            bizExtra: { extra: JSON.stringify({ table_id: table }) },
            bizPayload: { source: 'codex_new_task_attachment' },
            riskDetectionExtra: window.BitableDep.DriveHelper.getUploadRiskDetectionExtra(),
          };

          let taskId;
          try {
            taskId = await uploader.loadFile(file, opts);
          } catch (err) {
            return {
              ok: false,
              name: file.name,
              size: file.size,
              mimeType: file.type || 'application/octet-stream',
              error: String(err && (err.stack || err.message || err)),
              events,
            };
          }
          uploader.upload();

          const deadline = Date.now() + 180000;
          while (Date.now() < deadline) {
            const task = (uploader.tasks || []).find((item) => item.id === taskId) || uploader.tasks?.[0];
            if (task?.status === 3 && task.token) {
              return {
                ok: true,
                token: task.token,
                name: file.name,
                size: file.size,
                mimeType: file.type || 'application/octet-stream',
                timeStamp: Date.now(),
                successExtra: task.successExtra,
                dimensions,
                events,
              };
            }
            if (task?.status === 4 || task?.error) {
              return {
                ok: false,
                name: file.name,
                size: file.size,
                mimeType: file.type || 'application/octet-stream',
                error: task.error || 'upload failed',
                errorResponse: task.errorResponse,
                events,
              };
            }
            if (events.some((item) => item.event === 'parse_error' || item.event === 'runtime_incident_occurred')) {
              return {
                ok: false,
                name: file.name,
                size: file.size,
                mimeType: file.type || 'application/octet-stream',
                error: 'upload parse/runtime error',
                events,
              };
            }
            await new Promise((resolve) => setTimeout(resolve, 500));
          }
          return {
            ok: false,
            name: file.name,
            size: file.size,
            mimeType: file.type || 'application/octet-stream',
            error: 'upload timed out',
            events,
            tasks: (uploader.tasks || []).map((item) => ({
              id: item.id,
              name: item.name,
              status: item.status,
              token: item.token,
              error: item.error,
              uploadedSize: item.uploadedSize,
              totalSize: item.totalSize,
            })),
          };
        }
        """,
        {"table": group.TABLE_ID},
    )
    if not result.get("ok"):
        raise RuntimeError(f"Drive upload failed for {file_path.name}: {json.dumps(result, ensure_ascii=False)[:2000]}")
    return result


def attachment_cell(upload: dict[str, Any], file_path: Path) -> dict[str, Any]:
    token = str(upload["token"])
    mime_type = str(upload.get("mimeType") or mimetypes.guess_type(file_path.name)[0] or "application/octet-stream")
    item: dict[str, Any] = {
        "id": token,
        "attachmentToken": token,
        "timeStamp": int(upload.get("timeStamp") or 0),
        "name": file_path.name,
        "mimeType": mime_type,
        "size": int(upload.get("size") or file_path.stat().st_size),
    }
    dimensions = upload.get("dimensions")
    if isinstance(dimensions, dict):
        if dimensions.get("width"):
            item["width"] = int(dimensions["width"])
        if dimensions.get("height"):
            item["height"] = int(dimensions["height"])
    return {"type": 17, "value": [item]}


async def set_attachment_cell(page, target: AttachmentTarget, cell: dict[str, Any]) -> dict[str, Any]:
    field_id = group.FIELDS[target.field_key]
    result = await page.evaluate(
        """
        ({ table, view, recordId, fieldId, cell }) => {
          const result = window.bitableStore.commandManager.execute({
            cmd: 'SetRecords',
            tableId: table,
            viewId: view,
            data: { [recordId]: { [fieldId]: cell } },
            ignoreCheckRecordLoaded: true,
          });
          return JSON.parse(JSON.stringify(result, (key, value) => {
            if (typeof value === 'function') return '[function]';
            return value;
          }));
        }
        """,
        {
            "table": group.TABLE_ID,
            "view": group.VIEW_ID,
            "recordId": target.record_id,
            "fieldId": field_id,
            "cell": cell,
        },
    )
    if result.get("result") != 2:
        raise RuntimeError(f"SetRecords failed for {target.record_id} {target.field_label}: {result}")
    await page.wait_for_timeout(2500)
    return result


async def wait_for_server_file(page, target: AttachmentTarget, timeout_s: int = 60) -> None:
    deadline = asyncio.get_event_loop().time() + timeout_s
    while True:
        payload = await fetch_payload(page)
        record_map = summarize_by_id(payload)
        if not target_missing(record_map, target):
            return
        if asyncio.get_event_loop().time() > deadline:
            names = cell_files(record_map.get(target.record_id) or {}, target.field_key)
            raise RuntimeError(f"server did not show {target.file_name}; current files={names}")
        await asyncio.sleep(3)


async def run(plan_path: Path, apply: bool, verify_only: bool, limit: int, artifact_dir: Path | None = None) -> int:
    artifact_dir = (artifact_dir or infer_artifact_dir(plan_path)).resolve()
    plan = load_plan(plan_path)
    trial_rows = load_trial_rows(artifact_dir)
    targets = build_targets(plan, trial_rows, artifact_dir)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp(CDP_URL)
        pages = [page for ctx in browser.contexts for page in ctx.pages if group.BASE_TOKEN in page.url]
        if not pages:
            await browser.close()
            raise RuntimeError("target Bitable page is not open in the logged-in browser")
        page = pages[0]
        page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))
        await page.bring_to_front()
        await page.wait_for_function(
            "({ table }) => !!window.bitableStore?.modelOperator?.getTableById(table)",
            arg={"table": group.TABLE_ID},
            timeout=30000,
        )

        before_payload = await fetch_payload(page)
        before_path = group.write_backup(before_payload, "before_new_task_attachments")
        before_errors = validate_shapes_and_attachments(
            before_payload,
            plan,
            trial_rows,
            require_attachments=False,
        )
        if before_errors:
            print(f"before_backup={before_path}")
            for error in before_errors[:30]:
                print(f"ERROR: {error}")
            await browser.close()
            return 1

        record_map = summarize_by_id(before_payload)
        missing = [target for target in targets if target_missing(record_map, target)]
        print(f"plan={plan_path}")
        print(f"artifact_dir={artifact_dir}")
        print(f"before_backup={before_path}")
        print(f"targets={len(targets)} missing_attachments={len(missing)} apply={apply} verify_only={verify_only}")
        for target in missing[:80]:
            bnum = primary_number(record_map[target.record_id])
            print(f"  missing: {bnum} {target.record_id} {target.field_label} -> {target.file_name}")

        if verify_only or not apply:
            final_errors = validate_shapes_and_attachments(
                before_payload,
                plan,
                trial_rows,
                require_attachments=True,
            )
            if final_errors:
                print(f"attachment_verify_errors={len(final_errors)}")
                for error in final_errors[:80]:
                    print(f"  ERROR: {error}")
                await browser.close()
                return 1 if verify_only else 0
            print("attachment_verify_errors=0")
            await browser.close()
            return 0

        if limit > 0:
            missing = missing[:limit]
            print(f"limit={limit}; uploading first {len(missing)} missing attachment(s)")

        for index, target in enumerate(missing, 1):
            current_payload = await fetch_payload(page)
            current_map = summarize_by_id(current_payload)
            if not target_missing(current_map, target):
                print(f"[{index}/{len(missing)}] already present: {target.file_name}")
                continue
            bnum = primary_number(current_map[target.record_id])
            if not bnum:
                raise RuntimeError(f"cannot resolve primary number for {target.record_id}")
            print(f"[{index}/{len(missing)}] upload {bnum} {target.field_label} -> {target.file_name}")
            upload = await upload_drive_file(page, target.file_path)
            cell = attachment_cell(upload, target.file_path)
            result = await set_attachment_cell(page, target, cell)
            actions = result.get("operation", {}).get("actions", [])
            print(f"  SetRecords result={result.get('result')} actions={len(actions)} token={upload['token']}")
            await wait_for_server_file(page, target)
            print(f"  [OK] server verified {target.file_name}")

        after_payload = await fetch_payload(page)
        after_path = group.write_backup(after_payload, "after_new_task_attachments")
        final_errors = validate_shapes_and_attachments(
            after_payload,
            plan,
            trial_rows,
            require_attachments=True,
        )
        print(f"after_backup={after_path}")
        print(f"attachment_verify_errors={len(final_errors)}")
        for error in final_errors[:80]:
            print(f"  ERROR: {error}")
        await browser.close()
        return 1 if final_errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload/verify attachments for the fresh Bitable task group.")
    parser.add_argument("--plan", type=Path, help="new_task_group_plan_*.json path")
    parser.add_argument("--artifact-dir", type=Path, help="Directory containing trial_log.csv, repo.zip, Dockerfile, and patches")
    parser.add_argument("--apply", action="store_true", help="Upload missing attachments")
    parser.add_argument("--verify-only", action="store_true", help="Only verify; do not upload")
    parser.add_argument("--limit", type=int, default=0, help="Limit uploads for cautious resume/testing")
    args = parser.parse_args()
    plan_path = args.plan or latest_plan_path()
    return asyncio.run(
        run(plan_path, apply=args.apply, verify_only=args.verify_only, limit=args.limit, artifact_dir=args.artifact_dir)
    )


if __name__ == "__main__":
    raise SystemExit(main())
