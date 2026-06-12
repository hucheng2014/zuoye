import asyncio
import json
import os
from playwright.async_api import async_playwright


async def main():
    # Load all 35 rollout records
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rollout_data.json")
    with open(data_path, "r", encoding="utf-8") as f:
        rollouts = json.load(f)

    print(f"Loaded {len(rollouts)} rollout records from {data_path}")

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]

        # Find the Feishu page
        target_page = None
        for page in context.pages:
            url = page.url
            if "bytedance.larkoffice.com" in url:
                target_page = page
                break

        if not target_page:
            print("No Feishu/Lark page found at bytedance.larkoffice.com!")
            await browser.close()
            return

        title = await target_page.title()
        print(f"Found Lark page: {title}")
        await target_page.bring_to_front()
        await asyncio.sleep(2)

        # Close any open drawer first
        for _ in range(3):
            await target_page.keyboard.press("Escape")
            await asyncio.sleep(0.5)

        # ─── Helper: find a field row by its label ────────────────────────────
        async def get_row(field_name):
            """
            Scan all field wrapper elements for one whose label matches field_name.
            Scrolls the drawer down and retries up to 6 times if not found immediately.
            """
            wrapper_selectors = [
                ".base_record_card_field_editor_wrapper",
                ".bitable-node-container-wrapper-field",
                ".bitable-record-card-field-wrapper",
                ".bitable-field-item",
            ]
            combined = ", ".join(wrapper_selectors)

            for attempt in range(8):
                count = await target_page.locator(combined).count()
                for i in range(count):
                    row = target_page.locator(combined).nth(i)
                    label_loc = row.locator(
                        ".bitable-field-name, [class*='field-name'], [class*='field-label']"
                    ).first
                    if await label_loc.count() > 0:
                        text = await label_loc.inner_text()
                        text_clean = text.replace("​", "").strip().split("\n")[0]
                        if text_clean == field_name:
                            return row

                # Not found yet – scroll the record card drawer down and retry
                await target_page.evaluate(
                    """
                    () => {
                        const selectors = [
                            '.base-record-card',
                            '[class*="record-card"]',
                            '[class*="drawer-content"]',
                            '[class*="RecordCard"]',
                        ];
                        for (const sel of selectors) {
                            const el = document.querySelector(sel);
                            if (el) { el.scrollBy(0, 300); return; }
                        }
                        window.scrollBy(0, 300);
                    }
                    """
                )
                await asyncio.sleep(1)

            print(f"  [WARN] Field '{field_name}' not found after scrolling")
            return None

        # ─── Helper: fill a plain text / number field ─────────────────────────
        async def fill_text(field_name, value):
            short = value[:50] + "..." if len(value) > 50 else value
            print(f"  fill_text: '{field_name}' -> '{short}'")
            row = await get_row(field_name)
            if not row:
                print(f"  [ERROR] Row for '{field_name}' not found, skipping.")
                return
            await row.evaluate("el => el.scrollIntoView({ block: 'center' })")
            await asyncio.sleep(0.5)
            input_el = row.locator(
                "input, textarea, [class*='editor'], [contenteditable='true']"
            ).first
            await input_el.click(force=True)
            await asyncio.sleep(0.5)
            await target_page.keyboard.press("Control+A")
            await target_page.keyboard.press("Backspace")
            await target_page.keyboard.type(str(value))
            await asyncio.sleep(0.8)

        # ─── Helper: upload a file to an attachment field ─────────────────────
        async def upload_file(field_name, file_path):
            print(f"  upload_file: '{field_name}' -> '{os.path.basename(file_path)}'")
            if not os.path.exists(file_path):
                print(f"  [ERROR] File not found: {file_path}")
                return

            # Scroll to find the field first
            row = await get_row(field_name)
            if row:
                await row.evaluate("el => el.scrollIntoView({ block: 'center' })")
                await asyncio.sleep(0.8)

            # git_diff is ALWAYS the last attachment button in the form
            # Use global page locator, get the last one
            all_attach = target_page.locator(".b-collapsed-attach-editor__btn")
            cnt = await all_attach.count()
            if cnt == 0:
                print(f"  [ERROR] No attachment buttons found")
                return

            last_btn = all_attach.last
            await last_btn.scroll_into_view_if_needed()
            await asyncio.sleep(0.8)

            # Click WITHOUT force — triggers input#attachment-upload to appear
            try:
                await last_btn.click(timeout=5000)
            except Exception as e:
                print(f"  [WARN] Click failed ({e}), trying force")
                await last_btn.click(force=True)
            await asyncio.sleep(1.5)

            # Now input#attachment-upload should be visible
            try:
                await target_page.locator("input#attachment-upload").set_input_files(
                    file_path, timeout=8000
                )
                await asyncio.sleep(6)
                print(f"  [OK] Uploaded {os.path.basename(file_path)}")
            except Exception as e:
                print(f"  [ERROR] set_input_files failed: {e}")

        # ─── Main loop: add each rollout record ───────────────────────────────
        START_FROM = int(os.environ.get("START_FROM", "0"))
        for idx, data in enumerate(rollouts):
            if idx < START_FROM:
                continue
            prompt_idx = data["prompt_index"]
            rollout_id = data["rollout_id"]
            model = data["model_name"]
            session = data["session_id"]
            score = data["score"]
            reason = data["score_reason"]
            patch = data["patch_file"]

            print(
                f"\n{'='*60}\n"
                f"[{idx+1}/35] Prompt {prompt_idx} | Rollout {rollout_id} | {model}\n"
                f"{'='*60}"
            )

            # ── Step 1: Click "+ 添加记录" / "Add Record" button ──────────────
            add_btn_selectors = [
                '[data-e2e="bitable-add-record-btn"]',
                '.bitable-append-records-btn-wrapper button',
                'button:has-text("添加记录")',
                'button:has-text("Add Record")',
                '[class*="add-record"]',
            ]
            add_btn = None
            for sel in add_btn_selectors:
                try:
                    loc = target_page.locator(sel).first
                    if await loc.count() > 0:
                        add_btn = loc
                        break
                except Exception:
                    continue

            if not add_btn:
                print("  [ERROR] Cannot find 'Add Record' button, aborting this record.")
                continue

            await add_btn.click(force=True)
            print("  Clicked 'Add Record', waiting for drawer...")
            await asyncio.sleep(4)

            # ── Step 2: Fill text fields ──────────────────────────────────────
            await fill_text("prompt_index", prompt_idx)
            await fill_text("rollout_id", rollout_id)
            await fill_text("session_id", session)
            await fill_text("model_name", model)
            # score is a dropdown (0/1/2)
            try:
                score_row = await get_row("score")
                if score_row:
                    await score_row.evaluate("el => el.scrollIntoView({ block: 'center' })")
                    await asyncio.sleep(0.5)
                    trigger = score_row.locator(
                        ".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button'], "
                        ".bitable-select-view, .b-select-value-placeholder, [class*='select']"
                    ).first
                    await trigger.click(force=True)
                    await asyncio.sleep(1.5)
                    option = target_page.locator(
                        f".b-select-option, [class*='select-option'], [role='option']"
                    ).filter(has_text=score).first
                    await option.click(force=True)
                    await asyncio.sleep(1)
                    print(f"  score dropdown selected: {score}")
            except Exception as e:
                print(f"  [WARN] score dropdown failed ({e}), trying fill_text")
                await fill_text("score", score)
            await fill_text("score_reason", reason)

            # ── Step 3: Upload patch file to git_diff attachment field ────────
            await upload_file("git_diff", patch)

            # ── Step 4: Take a preview screenshot ────────────────────────────
            preview_path = (
                f"/Users/xaa/zuoye/traedocker/"
                f"rollout_p{prompt_idx}_r{rollout_id}_preview.png"
            )
            try:
                await target_page.screenshot(path=preview_path, timeout=5000)
                print(f"  Preview screenshot: {preview_path}")
            except Exception as e:
                print(f"  [WARN] Preview screenshot failed: {e}")

            # ── Step 5: Click Submit / 确定 ───────────────────────────────────
            submit_selectors = [
                "button:has-text('Submit')",
                "button:has-text('确定')",
                "button:has-text('Confirm')",
                "[class*='submit']",
                "[class*='confirm']",
            ]
            submitted = False
            for sel in submit_selectors:
                try:
                    btn = target_page.locator(sel).first
                    if await btn.count() > 0:
                        await btn.click(force=True)
                        submitted = True
                        print(f"  Clicked submit button ({sel})")
                        break
                except Exception:
                    continue

            if not submitted:
                print("  [WARN] Submit button not found, pressing Enter as fallback")
                await target_page.keyboard.press("Enter")

            await asyncio.sleep(5)

            # ── Step 6: Close drawer and pause before next record ─────────────
            for _ in range(3):
                await target_page.keyboard.press("Escape")
                await asyncio.sleep(0.5)

            # Extra cooldown between records
            await asyncio.sleep(2)

        # ─── Final screenshot ─────────────────────────────────────────────────
        final_path = "/Users/xaa/zuoye/traedocker/rollouts_all_submitted.png"
        try:
            await target_page.screenshot(path=final_path, timeout=10000)
            print(f"\nFinal screenshot saved to: {final_path}")
        except Exception as e:
            print(f"\n[WARN] Final screenshot failed: {e}")

        await browser.close()
        print("\nAll 35 rollout records submitted successfully!")


if __name__ == "__main__":
    asyncio.run(main())
