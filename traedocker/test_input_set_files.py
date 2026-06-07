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
            
        print(f"Target page: {await target_page.title()}")
        await target_page.bring_to_front()
        await asyncio.sleep(1)
        
        # Click Back to Edit if visible
        text = await target_page.evaluate("() => document.body.innerText")
        if "Back to Edit" in text:
            back_btn = target_page.locator("button:has-text('Back to Edit')").first
            await back_btn.click(force=True)
            await asyncio.sleep(2)
            
        # Ensure drawer is open
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        if not drawer_visible:
            print("Opening drawer...")
            await target_page.locator('[data-e2e="bitable-add-record-btn"]').first.click(force=True)
            await asyncio.sleep(3)
            
        # Find dockerfile row
        row = target_page.locator(".base_record_card_field_editor_wrapper, .bitable-field-item").filter(
            has=target_page.locator(".bitable-field-name, [class*='field-name']", has_text="dockerfile")
        ).first
        
        # Click the Add attachment button inside the row
        print("Clicking Add attachment inside the row...")
        await row.locator("button, .b-collapsed-attach-editor__btn, .bitable-card-edit-cell-editor-Attachment").first.click(force=True)
        await asyncio.sleep(1)
        
        # Directly set files on the global input element
        print("Directly setting files on input#attachment-upload...")
        await target_page.locator("input#attachment-upload").set_files("/home/jianglei/zuoye/traedocker/Dockerfile")
        
        # Sleep to allow upload
        print("Waiting 6 seconds for upload...")
        await asyncio.sleep(6)
        
        # Take screenshot of drawer
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/after_direct_upload.png", timeout=5000)
        print("Screenshot saved to after_direct_upload.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
