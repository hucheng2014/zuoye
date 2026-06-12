import asyncio
import json
import os
from playwright.async_api import async_playwright

async def main():
    with open("rollout_data.json", "r") as f:
        rollouts = json.load(f)

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        target_page = None
        for page in context.pages:
            url = page.url
            if "bytedance.larkoffice.com" in url:
                target_page = page
                break
                
        if not target_page:
            print("No Lark page found!")
            await browser.close()
            return
            
        print(f"Lark page: {await target_page.title()}")
        await target_page.bring_to_front()
        await asyncio.sleep(2)

        # Ensure drawer is closed initially
        for _ in range(3):
            await target_page.keyboard.press("Escape")
            await asyncio.sleep(0.5)

        async def get_row(field_name):
            wrapper_selectors = [
                ".base_record_card_field_editor_wrapper",
                ".bitable-node-container-wrapper-field",
                ".bitable-record-card-field-wrapper",
                ".bitable-field-item"
            ]
            for _ in range(6):
                count = await target_page.locator(", ".join(wrapper_selectors)).count()
                for i in range(count):
                    row = target_page.locator(", ".join(wrapper_selectors)).nth(i)
                    label_loc = row.locator(".bitable-field-name, [class*='field-name'], [class*='field-label']").first
                    if await label_loc.count() > 0:
                        text = await label_loc.inner_text()
                        text_clean = text.replace('\u200b', '').strip().split('\n')[0]
                        if text_clean == field_name:
                            return row
                
                await target_page.evaluate("""
                    () => {
                        const d = document.querySelector('.base-record-card, [class*="record-card"]');
                        if (d) d.scrollBy(0, 400);
                    }
                """)
                await asyncio.sleep(1)
                
            return None
            
        async def fill_text(field_name, value):
            print(f"Filling '{field_name}' -> '{value[:30]}...'")
            row = await get_row(field_name)
            if not row:
                print(f"Error: Row for {field_name} not found!")
                return
            await row.evaluate("el => el.scrollIntoView({ block: 'center' })")
            await asyncio.sleep(0.5)
            input_el = row.locator("input, textarea, [class*='editor'], [contenteditable='true']").first
            await input_el.click(force=True)
            await asyncio.sleep(0.5)
            await target_page.keyboard.press("Control+A")
            await target_page.keyboard.press("Backspace")
            await target_page.keyboard.type(value)
            await asyncio.sleep(1)
            
        async def select_dropdown(field_name, option_text):
            print(f"Selecting dropdown '{field_name}' -> '{option_text}'")
            row = await get_row(field_name)
            if not row:
                print(f"Error: Row for {field_name} not found!")
                return
            await row.evaluate("el => el.scrollIntoView({ block: 'center' })")
            await asyncio.sleep(0.5)
            trigger = row.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button'], .bitable-select-view, .b-select-value-placeholder").first
            await trigger.click(force=True)
            await asyncio.sleep(2)
            option = target_page.locator(".b-select-list .b-select-option, [class*='select-dropdown'] .b-select-option").filter(has_text=option_text).first
            await option.evaluate("el => el.scrollIntoView({ block: 'nearest' })")
            await asyncio.sleep(0.5)
            await option.click(force=True)
            await asyncio.sleep(1.5)

        for i, data in enumerate(rollouts[:2]): # test with 2 records first
            print(f"\n=== Adding Rollout {i+1} for Prompt {data['prompt_index']} ===")
            
            # Click Add Record
            add_btn = target_page.locator('[data-e2e="bitable-add-record-btn"], .bitable-append-records-btn-wrapper button').first
            await add_btn.click(force=True)
            await asyncio.sleep(4)
            
            # Select Parent Record - The Prompt's Record ID 
            # Note: We actually don't know the B-IDs of prompts 1-7. 
            # In Feishu, we usually search by the text or index.
            # But the requirement implies we should add them as child of parent OR fill the prompt_index.
            # I will fill the prompt_index to link them.
            
            await fill_text("prompt_index", data["prompt_index"])
            await fill_text("model_name", data["model_name"])
            await fill_text("score", data["score"])
            await fill_text("score_reason", data["score_reason"])
            await fill_text("session_id", data["session_id"])
            
            # Upload patch file
            patch_file = data["patch_file"]
            abs_path = os.path.abspath(patch_file)
            print(f"Uploading patch file: {abs_path}")
            row_patch = await get_row("git_diff")
            if row_patch:
                await row_patch.evaluate("el => el.scrollIntoView({ block: 'center' })")
                await asyncio.sleep(1)
                
                # Try clicking upload button
                upload_btn = row_patch.locator("button, .b-collapsed-attach-editor__btn, .bitable-card-edit-cell-editor-Attachment").first
                await upload_btn.click(force=True)
                await asyncio.sleep(2)
                
                try:
                    await target_page.set_input_files("input#attachment-upload", abs_path, timeout=5000)
                    print("Successfully set input files!")
                except Exception as e:
                    print("Failed to set input files:", e)
            else:
                print("git_diff field not found!")
            
            await asyncio.sleep(3)
            
            submit_btn = target_page.locator("button:has-text('Submit'), button:has-text('确定'), [class*='submit']").first
            await submit_btn.click(force=True)
            await asyncio.sleep(5)
            
            for _ in range(3):
                await target_page.keyboard.press("Escape")
                await asyncio.sleep(0.5)

        await browser.close()
        print("Done adding rollouts!")

if __name__ == "__main__":
    asyncio.run(main())
