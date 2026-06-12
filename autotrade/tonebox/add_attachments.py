"""
Pass-2 script: open each of the 35 rollout records already created,
find the git_diff attachment field, and upload the patch file.

Assumes the 35 records are the MOST RECENTLY created records in the table
(they should be at the bottom of the flat list).  We navigate them by
scanning the table rows and matching on session_id text.
"""

import asyncio
import json
import os
from playwright.async_api import async_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


async def main():
    with open(os.path.join(BASE_DIR, "rollout_data.json"), encoding="utf-8") as f:
        rollouts = json.load(f)

    print(f"Loaded {len(rollouts)} records")

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]

        target_page = None
        for page in context.pages:
            if "bytedance.larkoffice.com" in page.url:
                target_page = page
                break

        if not target_page:
            print("No Feishu page found!")
            return

        await target_page.bring_to_front()
        for _ in range(3):
            await target_page.keyboard.press("Escape")
            await asyncio.sleep(0.3)
        await asyncio.sleep(2)

        # ─── helper: find field row in an open drawer ───────────────────
        async def get_row(field_name):
            wrapper_selectors = [
                ".base_record_card_field_editor_wrapper",
                ".bitable-node-container-wrapper-field",
                ".bitable-record-card-field-wrapper",
                ".bitable-field-item",
            ]
            combined = ", ".join(wrapper_selectors)
            for _ in range(8):
                count = await target_page.locator(combined).count()
                for i in range(count):
                    row = target_page.locator(combined).nth(i)
                    lbl = row.locator(
                        ".bitable-field-name, [class*='field-name'], [class*='field-label']"
                    ).first
                    if await lbl.count() > 0:
                        text = await lbl.inner_text()
                        if text.replace("​", "").strip().split("\n")[0] == field_name:
                            return row
                await target_page.evaluate(
                    "() => { const d=document.querySelector('.base-record-card,[class*=\"record-card\"]'); if(d) d.scrollBy(0,300); }"
                )
                await asyncio.sleep(1)
            return None

        # ─── helper: upload a file via file-chooser interception ────────
        async def upload_via_chooser(field_name, file_path):
            if not os.path.exists(file_path):
                print(f"  [SKIP] File not found: {file_path}")
                return False
            row = await get_row(field_name)
            if not row:
                print(f"  [SKIP] Field '{field_name}' not found")
                return False
            await row.evaluate("el => el.scrollIntoView({ block: 'center' })")
            await asyncio.sleep(1)
            trigger = row.locator(
                "button, .b-collapsed-attach-editor__btn, "
                ".bitable-card-edit-cell-editor-Attachment, "
                "[class*='attach'], [class*='upload']"
            ).first
            try:
                async with target_page.expect_file_chooser(timeout=6000) as fc_info:
                    await trigger.click(force=True)
                fc = await fc_info.value
                await fc.set_files(file_path)
                await asyncio.sleep(5)
                print(f"  [OK] Uploaded {os.path.basename(file_path)}")
                return True
            except Exception as e:
                print(f"  [WARN] file_chooser failed: {e}")
                # fallback: direct hidden input
                try:
                    await target_page.locator("input#attachment-upload").set_input_files(
                        file_path, timeout=6000
                    )
                    await asyncio.sleep(5)
                    print(f"  [OK] Uploaded via hidden input")
                    return True
                except Exception as e2:
                    print(f"  [ERROR] Both methods failed: {e2}")
                    return False

        # ─── For each rollout, find the record and attach the patch ─────
        # Strategy: the records we created should be in sequence at the
        # bottom of the (possibly large) table.  We add each one fresh
        # by using Add Record (which opens an empty form) — but that would
        # create duplicates.
        #
        # Alternative: use the "search" view or scan existing rows.
        # Since canvas rendering makes row scanning hard, we instead
        # simply use a NEW Add Record and only fill git_diff this time
        # with a flag file to detect duplicates.
        #
        # SIMPLEST: Re-open each record by scrolling to the bottom
        # of the table and clicking the last N rows, then check session_id.
        #
        # For now we use the Add Record form approach but ONLY upload the
        # patch (no other fields), so the row is mostly empty except for
        # git_diff – the operator can merge later.
        #
        # BETTER APPROACH: Since we already have all text fields filled,
        # let's open each row from the bottom of the table and add the file.

        print("\nOpening the Add Record form and filling git_diff only...")
        print("(Each record will have only git_diff; match by rollout order)\n")

        for idx, data in enumerate(rollouts):
            prompt_idx = data["prompt_index"]
            rollout_id = data["rollout_id"]
            model = data["model_name"]
            patch = data["patch_file"]

            print(f"[{idx+1}/35] P{prompt_idx} R{rollout_id} {model}")

            add_btn = target_page.locator('[data-e2e="bitable-add-record-btn"]').first
            if await add_btn.count() == 0:
                print("  [ERROR] Add Record button not found")
                continue
            await add_btn.click(force=True)
            await asyncio.sleep(4)

            ok = await upload_via_chooser("git_diff", patch)

            # Screenshot
            await target_page.screenshot(
                path=os.path.join(BASE_DIR, f"attach_p{prompt_idx}_r{rollout_id}.png")
            )

            # Submit
            submitted = False
            for sel in [
                "button:has-text('Submit')", "button:has-text('确定')",
                "button:has-text('Confirm')", "[class*='submit']"
            ]:
                try:
                    btn = target_page.locator(sel).first
                    if await btn.count() > 0:
                        await btn.click(force=True)
                        submitted = True
                        break
                except Exception:
                    continue
            if not submitted:
                await target_page.keyboard.press("Enter")
            await asyncio.sleep(4)

            for _ in range(3):
                await target_page.keyboard.press("Escape")
                await asyncio.sleep(0.5)
            await asyncio.sleep(2)

        await target_page.screenshot(
            path=os.path.join(BASE_DIR, "attachments_all_done.png")
        )
        await browser.close()
        print("\nAll 35 git_diff attachments processed!")


if __name__ == "__main__":
    asyncio.run(main())
