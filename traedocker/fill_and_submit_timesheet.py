import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        # Select the Page without the invisible prefix (usually Page 2 in the pages list)
        target_page = None
        for idx, page in enumerate(context.pages):
            title = await page.title()
            if "需求二正式作业表_BBS" in title and not title.startswith("\u202d"):
                target_page = page
                print(f"Selected Page [{idx}]: {title}")
                break
                
        if not target_page:
            # fallback to first Lark page
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
        
        # Handle 'Back to Edit' dialog if showing
        text = await target_page.evaluate("() => document.body.innerText")
        if "Back to Edit" in text:
            print("Clicking 'Back to Edit'...")
            back_btn = target_page.locator("button:has-text('Back to Edit'), [class*='btn']:has-text('Back to Edit')").first
            await back_btn.click(force=True)
            await asyncio.sleep(2)
            
        # Check if drawer is open
        drawer_visible = await target_page.evaluate("""
            () => {
                const drawer = document.querySelector('.base-record-card, [class*="record-card"], [class*="drawer-content"]');
                return !!drawer;
            }
        """)
        
        if not drawer_visible:
            print("Drawer is closed. Clicking + Add Record to open it...")
            add_btn = target_page.locator('[data-e2e="bitable-add-record-btn"]').first
            await add_btn.click(force=True)
            await asyncio.sleep(4)
            
        # Helper to find a row by its field name
        async def get_row(field_name):
            # Try to match the exact field name
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
            # Use keyboard select all and type to replace existing text cleanly
            await target_page.keyboard.press("Control+A")
            await target_page.keyboard.press("Backspace")
            await target_page.keyboard.type(value)
            await asyncio.sleep(1)
            
        # Helper to select dropdown value
        async def select_dropdown(field_name, option_text):
            print(f"Selecting dropdown '{field_name}' -> '{option_text}'")
            row = await get_row(field_name)
            # Click the cell/value area to trigger dropdown
            await row.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button']").first.click(force=True)
            await asyncio.sleep(2)
            # Click the dropdown option in the overlay popup
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
            async with target_page.expect_file_chooser() as fc_info:
                await row.locator("text=Add attachment, [class*='add-attachment'], [class*='upload'], button").first.click(force=True)
            file_chooser = await fc_info.value
            await file_chooser.set_files(file_path)
            await asyncio.sleep(3)
            
        # Fill in the values!
        await fill_text("供应商", "长沙朗慧")
        await fill_text("repo_url", "无（业务方提供）")
        await select_dropdown("repo_type", "公有仓库")
        await select_dropdown("language", "Python")
        await upload_file("dockerfile", "/home/jianglei/zuoye/traedocker/Dockerfile")
        await upload_file("repo", "/home/jianglei/zuoye/traedocker/repo.zip")
        await fill_text("environment_notes", "Python 3.11, FastAPI, sqlite3")
        await fill_text("task_count", "7")
        await upload_file("dockerfile构建成功截图", "/home/jianglei/zuoye/traedocker/docker_build_success.png")
        
        # Wait extra time for all uploads to complete
        print("Waiting for all attachments to upload fully...")
        await asyncio.sleep(8)
        
        # Capture preview screenshot before submitting
        preview_path = "/home/jianglei/zuoye/traedocker/bbs_filled_preview.png"
        try:
            await target_page.screenshot(path=preview_path, timeout=5000)
            print(f"Preview screenshot saved to {preview_path}")
        except Exception as e:
            print("Preview screenshot failed:", e)
            
        # Click the Submit button
        print("Clicking Submit button...")
        submit_btn = target_page.locator("button:has-text('Submit'), button:has-text('确定'), [class*='submit']").first
        await submit_btn.click(force=True)
        await asyncio.sleep(5)
        
        # Capture final screenshot after submitting
        final_path = "/home/jianglei/zuoye/traedocker/bbs_after_submit.png"
        try:
            await target_page.screenshot(path=final_path, timeout=5000)
            print(f"Final screenshot saved to {final_path}")
        except Exception as e:
            print("Final screenshot failed:", e)
            
        await browser.close()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
