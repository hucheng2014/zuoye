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
        
        # Click Back to Edit if visible
        back_btn = target_page.locator("button:has-text('Back to Edit'), [class*='btn']:has-text('Back to Edit')")
        if await back_btn.count() > 0:
            print("Clicking 'Back to Edit'...")
            await back_btn.first.click(force=True)
            await asyncio.sleep(2)
            
        # Ensure drawer is open
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        if not drawer_visible:
            print("Opening drawer...")
            await target_page.locator('[data-e2e="bitable-add-record-btn"]').first.click(force=True)
            await asyncio.sleep(3)
            
        # Helper to find row
        async def get_row(field_name):
            return target_page.locator(".base_record_card_field_editor_wrapper, .bitable-field-item").filter(
                has=target_page.locator(".bitable-field-name, [class*='field-name']", has_text=field_name)
            ).first
            
        # Click upload button inside dockerfile row
        print("Scrolled to dockerfile row...")
        row_df = await get_row("dockerfile")
        await row_df.evaluate("el => el.scrollIntoView({ block: 'center' })")
        await asyncio.sleep(1)
        
        print("Clicking Add attachment...")
        await row_df.locator("button, .b-collapsed-attach-editor__btn, .bitable-card-edit-cell-editor-Attachment").first.click(force=True)
        await asyncio.sleep(2)
        
        # Check input existence
        exists = await target_page.evaluate("() => !!document.querySelector('input#attachment-upload')")
        print(f"input#attachment-upload exists: {exists}")
        
        if exists:
            # Set input files
            print("Setting input files...")
            await target_page.set_input_files("input#attachment-upload", "/home/jianglei/zuoye/traedocker/Dockerfile")
            print("Set input files successfully!")
            await asyncio.sleep(4)
            
            # Dismiss overlay
            await target_page.keyboard.press("Escape")
            await asyncio.sleep(1)
            
        # Take screenshot
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/step_4_only_upload.png")
        print("Screenshot saved to step_4_only_upload.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
