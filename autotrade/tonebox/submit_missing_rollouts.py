import asyncio
import argparse
import csv
import os
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


BASE_DIR = Path(__file__).resolve().parent
TABLE_ID = "tblcXB0RGGaHGm1r"
VIEW_ID = "vewxWP7trZ"
BASE_TOKEN = "B4SgbbhcyaJfwWsWHvcc1AtgnYd"

FIELDS = {
    "prompt_index": "fldW6rO2LU",
    "rollout_id": "fldqgS0GPQ",
    "session_id": "fldaMDOOJL",
    "model_name": "fldPxbX1x9",
    "score": "fldvFVIm4O",
    "score_reason": "fld7hrms66",
    "git_diff": "fld3Jhw2G1",
}

SELECT_OPTION_FIELDS = {"model_name", "score"}

MODEL_OPTION_TEXT = {
    "GPT-5.4": "GPT5.4",
    "Gemini 3.1 pro": "Gemini3.1pro",
    "DeepSeek-v4": "DeepSeekv4",
    "Doubao-Seed-2.0-Code": "Doubao-Seed-2.0-Code",
    "MinMax-M2.7": "MinMax-M2.7",
    "GLM-5.1": "GLM-5.1",
    "Qwen3.6-Plus": "Qwen3.6-Plus",
}

MODEL_ROLLOUT_ID = {
    "Doubao-Seed-2.0-Code": "1",
    "GPT-5.4": "2",
    "Gemini 3.1 pro": "3",
    "DeepSeek-v4": "4",
    "MinMax-M2.7": "5",
    "GLM-5.1": "5",
    "Qwen3.6-Plus": "5",
}


def load_rollouts():
    rows = []
    with (BASE_DIR / "trial_log.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["rollout_id"] = MODEL_ROLLOUT_ID.get(row["model"], "")
            if not row["rollout_id"]:
                raise ValueError(f"unknown rollout model: {row['model']}")
            row["patch_file"] = str(BASE_DIR / row["patch_file"])
            row["patch_name"] = Path(row["patch_file"]).name
            row["model_option"] = MODEL_OPTION_TEXT.get(row["model"], row["model"])
            rows.append(row)
    return rows


async def fetch_server_rows(page):
    return await page.evaluate(
        """
        async ({ token, table, view, fields, selectFields }) => {
          const tableObj = window.bitableStore.modelOperator.getTableById(table);
          const rev = tableObj.rev;
          const url = `/space/api/v1/bitable/${token}/records?tableId=${table}&viewId=${view}&tableRev=${rev}&depRev=%7B%7D&viewLazyLoad=true&offset=0&limit=3000&tableID=${table}&viewID=${view}&removeFmlExtra=true`;
          const json = await (await fetch(url, { credentials: 'include' })).json();
          const decoded = await window.unGzipBase64(json.data.records);
          const parsed = JSON.parse(decoded);
          const optionNames = {};
          for (const name of selectFields) {
            const field = tableObj.fields?.[fields[name]] || tableObj.fieldsMap?.get?.(fields[name]);
            optionNames[name] = Object.fromEntries((field?.property?.options || []).map(opt => [opt.id, opt.name]));
          }
          const unwrapText = (cell) => {
            if (!cell) return null;
            const value = cell.value ?? cell;
            if (value == null) return null;
            if (Array.isArray(value)) return value.map(x => x.text ?? x.name ?? '').join('');
            if (typeof value === 'string' || typeof value === 'number') return String(value);
            if (typeof value === 'object' && value.text) return String(value.text);
            if (typeof value === 'object' && value.name) return String(value.name);
            return null;
          };
          const unwrapSelect = (name, cell) => {
            if (!cell) return null;
            const value = cell.value ?? cell;
            if (value == null) return null;
            if (typeof value === 'string') return optionNames[name]?.[value] ?? value;
            if (Array.isArray(value)) return value.map(x => optionNames[name]?.[x] ?? x.name ?? x.text ?? x.id ?? '').join('');
            return null;
          };
          const unwrapFiles = (cell) => {
            if (!cell) return [];
            const value = cell.value ?? cell;
            if (value == null) return [];
            return Array.isArray(value) ? value.map(x => x.name ?? x.attachmentToken ?? x.id) : [];
          };
          return Object.entries(parsed.recordMap || {}).map(([recordId, rec]) => ({
            recordId,
            prompt_index: unwrapText(rec[fields.prompt_index]),
            rollout_id: unwrapText(rec[fields.rollout_id]),
            session_id: unwrapText(rec[fields.session_id]),
            model_name: unwrapSelect('model_name', rec[fields.model_name]),
            score: unwrapSelect('score', rec[fields.score]),
            score_reason: unwrapText(rec[fields.score_reason]),
            git_files: unwrapFiles(rec[fields.git_diff]),
          }));
        }
        """,
        {
            "token": BASE_TOKEN,
            "table": TABLE_ID,
            "view": VIEW_ID,
            "fields": FIELDS,
            "selectFields": list(SELECT_OPTION_FIELDS),
        },
    )


async def get_missing(page, rollouts):
    rows = await fetch_server_rows(page)
    by_sid = {row["session_id"]: row for row in rows if row.get("session_id")}
    missing = []
    wrong_git = []
    wrong_fields = []
    for rollout in rollouts:
        sid = rollout["session_id"]
        row = by_sid.get(sid)
        if not row:
            missing.append(rollout)
            continue

        field_diffs = []
        expected_values = {
            "prompt_index": rollout["prompt"],
            "rollout_id": rollout["rollout_id"],
            "model_name": rollout["model_option"],
            "score": rollout["score"],
            "score_reason": rollout["score_reason"],
        }
        for key, expected in expected_values.items():
            actual = row.get(key)
            if (actual or "") != (expected or ""):
                field_diffs.append((key, actual, expected))
        if field_diffs:
            wrong_fields.append((rollout, row, field_diffs))

        if rollout["patch_name"] not in row.get("git_files", []):
            wrong_git.append((rollout, row))
    return missing, wrong_git, wrong_fields, rows


async def close_overlays(page):
    for _ in range(3):
        await page.keyboard.press("Escape")
        await asyncio.sleep(0.25)
        for text in ["Exit", "退出"]:
            exit_btn = page.locator(f"button:visible:has-text('{text}')").first
            if await exit_btn.count():
                await exit_btn.click(force=True)
                await asyncio.sleep(1.0)
                return
    for text in ["Back to Edit", "返回编辑"]:
        btn = page.locator(f"button:visible:has-text('{text}')").first
        if await btn.count():
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.25)


async def reset_page(page):
    page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))
    await close_overlays(page)
    await page.reload(wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_function(
        "({ table }) => !!window.bitableStore?.modelOperator?.getTableById(table)",
        arg={"table": TABLE_ID},
        timeout=30000,
    )
    await asyncio.sleep(2)


async def get_field_row(page, field_name):
    wrappers = [
        ".base_record_card_field_editor_wrapper",
        ".bitable-node-container-wrapper-field",
        ".bitable-record-card-field-wrapper",
        ".bitable-field-item",
        "[class*='field-editor-wrapper']",
        "[class*='field-wrapper']",
    ]
    selector = ", ".join(wrappers)
    for _ in range(14):
        count = await page.locator(selector).count()
        for i in range(count):
            row = page.locator(selector).nth(i)
            label = row.locator(".bitable-field-name, [class*='field-name'], [class*='field-label']").first
            if await label.count():
                raw = (await label.inner_text()).replace("\u200b", "").strip().split("\n")[0]
                if raw == field_name:
                    await row.evaluate("el => el.scrollIntoView({ block: 'center', inline: 'nearest' })")
                    try:
                        await row.scroll_into_view_if_needed(timeout=4000)
                    except PlaywrightTimeoutError:
                        pass
                    await asyncio.sleep(0.35)
                    return row
        await page.evaluate(
            """
            () => {
              const sels = ['.base-record-card', '[class*="record-card"]', '[class*="drawer-content"]', '[class*="CardModal"]'];
              for (const sel of sels) {
                const el = document.querySelector(sel);
                if (el && el.scrollHeight > el.clientHeight) { el.scrollBy(0, 420); return; }
              }
            }
            """
        )
        await asyncio.sleep(0.35)
    return None


async def fill_text(page, field_name, value):
    row = await get_field_row(page, field_name)
    if not row:
        raise RuntimeError(f"field not found: {field_name}")
    box = await row.bounding_box()
    if not box:
        raise RuntimeError(f"field is not visible: {field_name}")
    text = str(value)
    for attempt in range(3):
        target_box = await row.evaluate(
            """
            (el) => {
              const selectors = [
                '[contenteditable="true"]',
                'textarea',
                'input:not(.hidden-input):not([readonly])',
                '.b-field-label__editor',
                '[class*="editor"]'
              ];
              const isVisible = (node) => {
                const r = node.getBoundingClientRect();
                const style = getComputedStyle(node);
                return r.width > 0 && r.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
              };
              const target = Array.from(el.querySelectorAll(selectors.join(','))).find(isVisible);
              if (target) {
                const r = target.getBoundingClientRect();
                return { x: r.left + Math.min(r.width - 8, Math.max(8, r.width / 2)), y: r.top + r.height / 2 };
              }
              const r = el.getBoundingClientRect();
              return { x: r.left + Math.min(r.width - 24, 210), y: r.top + r.height / 2 };
            }
            """
        )
        await page.mouse.click(target_box["x"], target_box["y"])
        await asyncio.sleep(0.25)
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await page.keyboard.insert_text(text)
        await page.keyboard.press("Tab")
        await asyncio.sleep(0.5)
        if await row_contains_value(row, text):
            return
        if attempt == 2:
            raise RuntimeError(f"text not entered: {field_name}")
        await asyncio.sleep(0.3)


async def visible_text_of_row(row):
    try:
        return (await row.inner_text(timeout=3000)).replace("\u200b", "").strip()
    except PlaywrightTimeoutError:
        return ""


async def row_contains_value(row, value):
    return await row.evaluate(
        """
        (el, expected) => {
          const normalize = (s) => String(s || '').replace(/\\u200b/g, '').trim();
          const isVisible = (node) => {
            const r = node.getBoundingClientRect();
            const style = getComputedStyle(node);
            return r.width > 0 && r.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
          };
          const values = [el.innerText];
          for (const node of el.querySelectorAll('input, textarea, [contenteditable="true"]')) {
            if (!isVisible(node)) continue;
            values.push(node.value || node.innerText || node.textContent || '');
          }
          return values.map(normalize).some(v => v.includes(expected));
        }
        """,
        str(value),
    )


async def select_option(page, field_name, visible_text):
    row = await get_field_row(page, field_name)
    if not row:
        raise RuntimeError(f"field not found: {field_name}")
    box = await row.bounding_box()
    if not box:
        raise RuntimeError(f"field is not visible: {field_name}")
    for attempt in range(3):
        await page.mouse.click(box["x"] + min(box["width"] - 24, 210), box["y"] + box["height"] / 2)
        await asyncio.sleep(0.8)
        for scroll_attempt in range(6):
            option_box = await page.evaluate(
                """
                (text) => {
                  const selectors = [
                    '[role="option"]',
                    '.b-select-option',
                    '.ud__select-option',
                    '[class*="select-option"]',
                    '[class*="SelectOption"]'
                  ];
                  const isVisible = (el) => {
                    const r = el.getBoundingClientRect();
                    const style = getComputedStyle(el);
                    return r.width > 0 && r.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
                  };
                  const normalize = (s) => (s || '').replace(/\\u200b/g, '').trim();
                  const candidates = Array.from(document.querySelectorAll(selectors.join(',')))
                    .filter(isVisible)
                    .map(el => {
                      const r = el.getBoundingClientRect();
                      const lines = normalize(el.innerText).split('\\n').map(normalize).filter(Boolean);
                      return { el, lines, area: r.width * r.height };
                    })
                    .filter(item => item.lines.length === 1 && item.lines[0] === text)
                    .sort((a, b) => a.area - b.area);
                  const item = candidates[0];
                  if (!item) return null;
                  item.el.scrollIntoView({ block: 'center', inline: 'nearest' });
                  const r = item.el.getBoundingClientRect();
                  return { x: r.left + r.width / 2, y: r.top + r.height / 2, text: normalize(item.el.innerText) };
                }
                """,
                visible_text,
            )
            if option_box:
                await page.mouse.click(option_box["x"], option_box["y"])
                await asyncio.sleep(0.8)
                row_text = await visible_text_of_row(row)
                if visible_text in row_text:
                    return
                break
            await page.evaluate(
                """
                () => {
                  const selectors = [
                    '[role="listbox"]',
                    '.b-select-dropdown-container',
                    '.ud__select-menu',
                    '[class*="select-dropdown"]',
                    '[class*="dropdown-container"]'
                  ];
                  const isVisible = (el) => {
                    const r = el.getBoundingClientRect();
                    const style = getComputedStyle(el);
                    return r.width > 0 && r.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
                  };
                  const scrollers = Array.from(document.querySelectorAll(selectors.join(',')))
                    .filter(isVisible)
                    .filter(el => el.scrollHeight > el.clientHeight);
                  for (const el of scrollers) el.scrollBy(0, 180);
                }
                """
            )
            await page.mouse.wheel(0, 180)
            await asyncio.sleep(0.25)
        await page.keyboard.press("Escape")
        await asyncio.sleep(0.4)
    raise RuntimeError(f"option not selected: {field_name} -> {visible_text}")


async def upload_patch(page, patch_path):
    if not Path(patch_path).exists():
        raise FileNotFoundError(patch_path)
    row = await get_field_row(page, "git_diff")
    if not row:
        raise RuntimeError("field not found: git_diff")
    patch_name = Path(patch_path).name
    for attempt in range(3):
        await row.evaluate("el => el.scrollIntoView({ block: 'center', inline: 'nearest' })")
        await asyncio.sleep(0.5)
        click_box = await row.evaluate(
            """
            (el) => {
              const selectors = [
                '.b-collapsed-attach-editor__btn',
                'button',
                '[class*="attach"][class*="btn"]',
                '[class*="Attachment"]'
              ];
              const isVisible = (node) => {
                const r = node.getBoundingClientRect();
                const style = getComputedStyle(node);
                return r.width > 0 && r.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
              };
              const candidates = Array.from(el.querySelectorAll(selectors.join(','))).filter(isVisible);
              const target = candidates.find(node => /add attachment/i.test(node.innerText || '')) || candidates[0];
              if (target) {
                const r = target.getBoundingClientRect();
                return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
              }
              const r = el.getBoundingClientRect();
              return { x: r.left + Math.min(r.width - 24, 210), y: r.top + r.height / 2 };
            }
            """
        )
        try:
            async with page.expect_file_chooser(timeout=8000) as chooser_info:
                await page.mouse.click(click_box["x"], click_box["y"])
            chooser = await chooser_info.value
            await chooser.set_files(patch_path)
        except PlaywrightTimeoutError:
            file_input = page.locator("input#attachment-upload, input[type='file']").last
            if await file_input.count() == 0:
                if attempt == 2:
                    raise RuntimeError("attachment file input did not appear")
                continue
            await file_input.set_input_files(patch_path, timeout=10000)

        await page.wait_for_function(
            """
            (name) => document.body.innerText.includes(name)
            """,
            arg=patch_name,
            timeout=30000,
        )
        await asyncio.sleep(1.0)
        return
    raise RuntimeError(f"upload failed: {patch_name}")


async def submit_drawer(page):
    for text in ["Submit", "确定", "Confirm"]:
        btn = page.locator(f"button:has-text('{text}')").first
        if await btn.count():
            await btn.click(force=True)
            await asyncio.sleep(4)
            return
    await page.keyboard.press("Enter")
    await asyncio.sleep(4)


async def open_add_record(page):
    await close_overlays(page)
    selectors = [
        "[data-e2e='bitable-add-record-btn']",
        ".bitable-append-records-btn-wrapper button",
        "button:has-text('Add Record')",
        "button:has-text('添加记录')",
        "[class*='add-record']",
    ]
    for selector in selectors:
        loc = page.locator(selector).first
        if await loc.count():
            await loc.click(force=True)
            await asyncio.sleep(3)
            return
    raise RuntimeError("Add Record button not found")


async def create_one(page, rollout):
    await open_add_record(page)
    await fill_text(page, "prompt_index", rollout["prompt"])
    await fill_text(page, "rollout_id", rollout["rollout_id"])
    await fill_text(page, "session_id", rollout["session_id"])
    await select_option(page, "model_name", MODEL_OPTION_TEXT.get(rollout["model"], rollout["model"]))
    await select_option(page, "score", rollout["score"])
    await fill_text(page, "score_reason", rollout["score_reason"])
    await upload_patch(page, rollout["patch_file"])
    await submit_drawer(page)
    await close_overlays(page)


async def run(verify_only=False):
    rollouts = load_rollouts()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:9235")
        page = [p for p in browser.contexts[0].pages if "larkoffice" in p.url][0]
        await page.bring_to_front()
        await reset_page(page)

        missing, wrong_git, wrong_fields, rows = await get_missing(page, rollouts)
        print(
            f"Server rows: {len(rows)}; missing records: {len(missing)}; "
            f"wrong git: {len(wrong_git)}; wrong fields: {len(wrong_fields)}"
        )
        for item in missing:
            print(f"  missing: P{item['prompt']} R{item['rollout_id']} {item['model']} {item['session_id']} {item['patch_name']}")
        if wrong_git:
            print("Records with wrong/missing git_diff already exist:")
            for rollout, row in wrong_git:
                print(f"  {row['recordId']} {rollout['session_id']} has {row.get('git_files')}, expected {rollout['patch_name']}")
        if wrong_fields:
            print("Records with field mismatches already exist:")
            for rollout, row, diffs in wrong_fields[:30]:
                detail = "; ".join(f"{key}: {actual!r} != {expected!r}" for key, actual, expected in diffs)
                print(f"  {row['recordId']} P{rollout['prompt']} R{rollout['rollout_id']} {rollout['session_id']}: {detail}")
        if verify_only:
            await browser.close()
            if missing or wrong_git or wrong_fields:
                return 1
            return 0

        if not missing:
            await browser.close()
            if wrong_git or wrong_fields:
                return 1
            return 0

        max_create = int(os.environ.get("MAX_CREATE", "0") or "0")
        if max_create > 0:
            missing = missing[:max_create]
            print(f"MAX_CREATE={max_create}; limiting this run to {len(missing)} record(s)")

        for idx, rollout in enumerate(missing, 1):
            print(f"\\n[{idx}/{len(missing)}] Creating P{rollout['prompt']} R{rollout['rollout_id']} {rollout['model']}")
            try:
                await create_one(page, rollout)
            except Exception as exc:
                print(f"  [ERROR] create failed: {exc}")
                await page.screenshot(path=str(BASE_DIR / f"missing_create_error_{idx}.png"))
                await close_overlays(page)
                continue

            check_missing, check_wrong_git, check_wrong_fields, _ = await get_missing(page, rollouts)
            still_missing = {item["session_id"] for item in check_missing}
            still_wrong = {item["session_id"] for item, _row in check_wrong_git}
            still_wrong_fields = {item["session_id"] for item, _row, _diffs in check_wrong_fields}
            if (
                rollout["session_id"] not in still_missing
                and rollout["session_id"] not in still_wrong
                and rollout["session_id"] not in still_wrong_fields
            ):
                print("  [OK] verified on server")
            else:
                print("  [WARN] not verified yet on server")

        final_missing, final_wrong_git, final_wrong_fields, final_rows = await get_missing(page, rollouts)
        print(
            f"\\nFINAL server rows: {len(final_rows)}; missing records: {len(final_missing)}; "
            f"wrong git: {len(final_wrong_git)}; wrong fields: {len(final_wrong_fields)}"
        )
        for item in final_missing:
            print(f"  still missing: P{item['prompt']} R{item['rollout_id']} {item['session_id']}")
        for item, row in final_wrong_git:
            print(f"  wrong git: {row['recordId']} {item['session_id']} expected {item['patch_name']}")
        for item, row, diffs in final_wrong_fields[:30]:
            detail = "; ".join(f"{key}: {actual!r} != {expected!r}" for key, actual, expected in diffs)
            print(f"  wrong fields: {row['recordId']} P{item['prompt']} R{item['rollout_id']} {item['session_id']}: {detail}")
        await page.screenshot(path=str(BASE_DIR / "submit_missing_final.png"), full_page=False)
        await browser.close()
        if final_missing or final_wrong_git or final_wrong_fields:
            return 1
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create or verify rollout rows in Bitable.")
    parser.add_argument("--verify-only", action="store_true", help="Only re-read and verify server rows; do not create records.")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(verify_only=args.verify_only)))
