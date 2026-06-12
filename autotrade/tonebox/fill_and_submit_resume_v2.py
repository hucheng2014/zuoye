import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        # Select target page
        target_page = None
        for idx, page in enumerate(context.pages):
            title = await page.title()
            if "需求二正式作业表_BBS" in title and not title.startswith("\u202d"):
                target_page = page
                print(f"Selected Page [{idx}]: {title}")
                break
                
        if not target_page:
            for idx, page in enumerate(context.pages):
                url = page.url
                if "bytedance.larkoffice.com" in url:
                    target_page = page
                    print(f"Fallback to Page [{idx}]: {await page.title()}")
                    break
                    
        if not target_page:
            print("No Lark page found!")
            await browser.close()
            return
            
        await target_page.bring_to_front()
        await asyncio.sleep(2)
        
        # Helper to find a row by its field name
        async def get_row(field_name):
            row = target_page.locator(".base_record_card_field_editor_wrapper, .bitable-field-item").filter(
                has=target_page.locator(".bitable-field-name, [class*='field-name'], [class*='field-label']", has_text=field_name)
            ).first
            return row
            
        # Helper to fill text field
        async def fill_text(field_name, value):
            print(f"Filling '{field_name}' -> '{value}'")
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
            print(f"Selecting dropdown '{field_name}' -> '{option_text}'")
            row = await get_row(field_name)
            await row.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button']").first.click(force=True)
            await asyncio.sleep(2)
            option = target_page.locator(".ud__select-option, [role='option'], .ud__dropdown-menu-item, div").filter(has_text=option_text).first
            await option.click(force=True)
            await asyncio.sleep(1)
            await target_page.keyboard.press("Escape")
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
            await asyncio.sleep(1)
            # Click upload trigger
            await row.locator("button, .b-collapsed-attach-editor__btn, .bitable-card-edit-cell-editor-Attachment").first.click(force=True)
            await asyncio.sleep(1.5)
            # Direct upload via global input
            await target_page.locator("input#attachment-upload").set_input_files(file_path)
            await asyncio.sleep(4)
            # Dismiss overlay
            await target_page.keyboard.press("Escape")
            await asyncio.sleep(1)
            
        # Click 'Back to Edit' to close warning dialog if showing
        print("Locating Back to Edit button...")
        back_btn = target_page.locator("button:has-text('Back to Edit'), [class*='btn']:has-text('Back to Edit')")
        if await back_btn.count() > 0:
            print("Clicking 'Back to Edit'...")
            await back_btn.first.click(force=True)
            await asyncio.sleep(3)
        else:
            print("Back to Edit button not found.")
            
        # Verify drawer is open
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"], [class*="drawer-content"]');
        """)
        print(f"Is drawer visible? {drawer_visible}")
        if not drawer_visible:
            print("Drawer is not open. Opening a new record...")
            add_btn = target_page.locator('[data-e2e="bitable-add-record-btn"], .bitable-append-records-btn-wrapper button').first
            await add_btn.click(force=True)
            await asyncio.sleep(4)
            # Fill vendor and repo_url if we opened a fresh record
            await fill_text("供应商", "长沙朗慧")
            await fill_text("repo_url", "无（业务方提供）")
            
        # Fill remaining fields
        await select_dropdown("repo_type", "公有仓库")
        await select_dropdown("language", "Python")
        
        # Upload attachments
        await upload_file("dockerfile", "/Users/xaa/zuoye/traedocker/Dockerfile")
        await upload_file("repo", "/Users/xaa/zuoye/traedocker/repo.zip")
        
        await fill_text("environment_notes", "Python 3.11, FastAPI, sqlite3")
        await fill_text("task_count", "7")
        
        await upload_file("dockerfile构建成功截图", "/Users/xaa/zuoye/traedocker/docker_build_success.png")
        
        print("Waiting for all attachments to upload fully...")
        await asyncio.sleep(8)
        
        # Capture preview screenshot before submitting
        preview_path = "/Users/xaa/zuoye/traedocker/bbs_filled_preview.png"
        try:
            await target_page.screenshot(path=preview_path, timeout=5000)
            print(f"Preview screenshot saved to {preview_path}")
        except Exception as e:
            print("Preview screenshot failed:", e)
            
        # Click the Submit button
        print("Clicking Submit button...")
        submit_btn = target_page.locator("button:has-text('Submit'), button:has-text('确定'), [class*='submit']").first
        await submit_btn.click(force=True)
        await asyncio.sleep(6)
        
        # Capture final screenshot after submitting
        final_path = "/Users/xaa/zuoye/traedocker/bbs_after_submit.png"
        try:
            await target_page.screenshot(path=final_path, timeout=5000)
            print(f"Final screenshot saved to {final_path}")
        except Exception as e:
            print("Final screenshot failed:", e)
            
        await browser.close()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
