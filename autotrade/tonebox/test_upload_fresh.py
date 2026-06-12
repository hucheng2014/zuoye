import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        target_page = None
        for page in context.pages:
            title = await page.title()
            if "需求二正式作业表_BBS" in title and not title.startswith("\u202d"):
                target_page = page
                break
        if not target_page:
            target_page = context.pages[0]
            
        await target_page.bring_to_front()
        await asyncio.sleep(1)
        
        # Ensure drawer is open
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        if not drawer_visible:
            await target_page.locator('[data-e2e="bitable-add-record-btn"]').first.click(force=True)
            await asyncio.sleep(3)
            
        # Helper to find row
        async def get_row(field_name):
            row = target_page.locator(".base_record_card_field_editor_wrapper, .bitable-field-item").filter(
                has=target_page.locator(".bitable-field-name, [class*='field-name']", has_text=field_name)
            ).first
            return row

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
            # Click upload trigger
            await row.locator("button, .b-collapsed-attach-editor__btn, .bitable-card-edit-cell-editor-Attachment").first.click(force=True)
            await asyncio.sleep(1.5)
            # Direct upload via global input
            await target_page.locator("input#attachment-upload").set_input_files(file_path)
            await asyncio.sleep(4)
            # Close/dismiss any overlay
            await target_page.keyboard.press("Escape")
            await asyncio.sleep(1)

        await upload_file("dockerfile", "/Users/xaa/zuoye/traedocker/Dockerfile")
        await upload_file("repo", "/Users/xaa/zuoye/traedocker/repo.zip")
        
        # Take screenshot
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/step_2_upload.png")
        print("Screenshot saved to step_2_upload.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
