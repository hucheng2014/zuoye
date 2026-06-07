import asyncio
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
                break
        if not target_page:
            target_page = context.pages[0]
            
        print(f"Target page: {await target_page.title()}")
        await target_page.bring_to_front()
        
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
        
        # Scroll row to center of view using JS scroll
        print("Scrolling row into view...")
        await row.evaluate("el => el.scrollIntoView({ block: 'center' })")
        await asyncio.sleep(1)
        
        # Test 1: Click the cell editor wrapper
        print("Testing click on .bitable-card-edit-cell-editor-Attachment...")
        try:
            async with target_page.expect_file_chooser(timeout=5000) as fc_info:
                # Hover to be sure
                await row.locator(".bitable-card-edit-cell-editor-Attachment").first.hover()
                await asyncio.sleep(0.5)
                await row.locator(".bitable-card-edit-cell-editor-Attachment").first.click(force=True)
            print("SUCCESS: Clicked .bitable-card-edit-cell-editor-Attachment triggered file chooser!")
            await browser.close()
            return
        except Exception as e:
            print("FAILED:", e)
            
        # Test 2: Click the button
        print("Testing click on button...")
        try:
            async with target_page.expect_file_chooser(timeout=5000) as fc_info:
                # Hover to be sure
                await row.locator("button").first.hover()
                await asyncio.sleep(0.5)
                await row.locator("button").first.click(force=True)
            print("SUCCESS: Clicked button triggered file chooser!")
            await browser.close()
            return
        except Exception as e:
            print("FAILED:", e)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
