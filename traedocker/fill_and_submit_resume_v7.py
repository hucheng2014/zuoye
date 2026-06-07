import asyncio
import os
import re
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print("Connecting to browser over CDP...")
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        target_page = None
        for idx, page in enumerate(context.pages):
            title = await page.title()
            if "需求二正式作业表_BBS" in title and not title.startswith("\u202d"):
                target_page = page
                print(f"Selected Page [{idx}]: {title}")
                break
                
        if not target_page:
            target_page = context.pages[0]
            print(f"Fallback to Page [0]: {await target_page.title()}")
            
        await target_page.bring_to_front()
        await asyncio.sleep(2)
        
        # 1. Close warning dialog if visible
        back_btn = target_page.locator("button:has-text('Back to Edit'), [class*='btn']:has-text('Back to Edit')")
        if await back_btn.count() > 0:
            print("Warning popup detected. Clicking 'Back to Edit'...")
            await back_btn.first.click(force=True)
            await asyncio.sleep(3)
            
        # 2. Check if drawer is open using Submit button visibility
        drawer_visible = await target_page.locator("button:has-text('Submit'), button:has-text('确定')").count() > 0
        print(f"Is drawer open? {drawer_visible}")
        
        if not drawer_visible:
            print("Drawer is closed. Clicking + Add Record to open a new record...")
            add_btn = target_page.locator('[data-e2e="bitable-add-record-btn"], .bitable-append-records-btn-wrapper button').first
            await add_btn.click(force=True)
            await asyncio.sleep(5)
            
        # Helper to find a row by its field name exactly
        async def get_row(field_name):
            wrapper_selectors = [
                ".bitable-node-container-wrapper-field",
                ".base_record_card_field_editor_wrapper",
                ".bitable-record-card-field-wrapper",
                ".bitable-field-item"
            ]
            count = await target_page.locator(", ".join(wrapper_selectors)).count()
            for i in range(count):
                row = target_page.locator(", ".join(wrapper_selectors)).nth(i)
                label_loc = row.locator(".bitable-field-name, [class*='field-name'], [class*='field-label']").first
                if await label_loc.count() > 0:
                    text = await label_loc.inner_text()
                    # Strip whitespace, newlines, and zero-width spaces
                    text_clean = text.replace('\u200b', '').strip().split('\n')[0]
                    if text_clean == field_name:
                        return row
            # Fallback to substring matching if exact match fails
            print(f"Exact match failed for '{field_name}', falling back to substring locator...")
            return target_page.locator(".base_record_card_field_editor_wrapper, .bitable-field-item").filter(
                has=target_page.locator(".bitable-field-name, [class*='field-name'], [class*='field-label']", has_text=field_name)
            ).first
            
        # Helper to fill text field
        async def fill_text(field_name, value):
            print(f"Filling text: '{field_name}' -> '{value}'")
            row = await get_row(field_name)
            input_el = row.locator("input, textarea, [class*='editor'], [contenteditable='true']").first
            await input_el.click(force=True)
            await asyncio.sleep(0.5)
            await target_page.keyboard.press("Control+A")
            await target_page.keyboard.press("Backspace")
            await target_page.keyboard.type(value)
            await asyncio.sleep(1)
            
        # Helper to select dropdown value
        async def select_dropdown(field_name, option_text):
            print(f"Selecting dropdown: '{field_name}' -> '{option_text}'")
            row = await get_row(field_name)
            trigger = row.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button']").first
            await trigger.click(force=True)
            await asyncio.sleep(2)
            
            # Select option from active visible dropdown container only (no force click)
            option = target_page.locator(".b-select-dropdown-container").locator(".b-select-option").filter(has_text=option_text).first
            await option.click()
            await asyncio.sleep(1.5)
            
            # Click row label to close dropdown safely without Esc key
            label = row.locator(".bitable-field-name, [class*='field-name']").first
            await label.click(force=True)
            await asyncio.sleep(1)
            
        # Helper to upload file
        async def upload_file(field_name, file_path):
            print(f"Uploading file for '{field_name}' -> '{file_path}'")
            if not os.path.exists(file_path):
                print(f"ERROR: File does not exist at {file_path}!")
                return
            row = await get_row(field_name)
            # Scroll row into view
            await row.evaluate("el => el.scrollIntoView({ block: 'center' })")
            await asyncio.sleep(1.5)
            
            # Click Add attachment trigger inside the row
            trigger = row.locator("button, .b-collapsed-attach-editor__btn, .bitable-card-edit-cell-editor-Attachment").first
            await trigger.click(force=True)
            await asyncio.sleep(2)
            
            # Set files directly on global input
            await target_page.set_input_files("input#attachment-upload", file_path)
            await asyncio.sleep(6) # Wait for upload progress to complete
            
            # Close upload overlay by clicking the row label instead of Escape key
            label = row.locator(".bitable-field-name, [class*='field-name']").first
            await label.click(force=True)
            await asyncio.sleep(1.5)

        # 3. Fill text and dropdowns
        await fill_text("供应商", "长沙朗慧")
        await fill_text("repo_url", "无（业务方提供）")
        await select_dropdown("repo_type", "公有仓库")
        await select_dropdown("language", "Python")
        
        # 4. Upload core code files
        await upload_file("dockerfile", "/home/jianglei/zuoye/traedocker/Dockerfile")
        await upload_file("repo", "/home/jianglei/zuoye/traedocker/repo.zip")
        
        # 5. Fill remaining details
        await fill_text("environment_notes", "Python 3.11, FastAPI, sqlite3")
        await fill_text("task_count", "7")
        
        # 6. Upload success screenshot
        await upload_file("dockerfile构建成功截图", "/home/jianglei/zuoye/traedocker/docker_build_success.png")
        
        print("Waiting for all uploads and fields to stabilize...")
        await asyncio.sleep(8)
        
        # Capture preview screenshot before submitting
        preview_path = "/home/jianglei/zuoye/traedocker/bbs_filled_preview.png"
        try:
            await target_page.screenshot(path=preview_path, timeout=5000)
            print(f"Preview screenshot saved to {preview_path}")
        except Exception as e:
            print("Preview screenshot failed:", e)
            
        # 7. Submit
        print("Clicking Submit button...")
        submit_btn = target_page.locator("button:has-text('Submit'), button:has-text('确定'), [class*='submit']").first
        await submit_btn.click(force=True)
        await asyncio.sleep(8)
        
        # Capture final screenshot after submitting
        final_path = "/home/jianglei/zuoye/traedocker/bbs_after_submit.png"
        try:
            await target_page.screenshot(path=final_path, timeout=5000)
            print(f"Final screenshot saved to {final_path}")
        except Exception as e:
            print("Final screenshot failed:", e)
            
        await browser.close()
        print("Flow finished successfully!")

if __name__ == "__main__":
    asyncio.run(main())
