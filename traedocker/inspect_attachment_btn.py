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
            
        # Get the HTML of the dockerfile row
        row_html = await target_page.evaluate("""
            () => {
                const items = document.querySelectorAll('.base_record_card_field_editor_wrapper, .bitable-field-item');
                for (let item of items) {
                    const labelEl = item.querySelector('.bitable-field-name, [class*="field-name"]');
                    if (labelEl && labelEl.innerText.includes('dockerfile')) {
                        return item.outerHTML;
                    }
                }
                return 'ROW NOT FOUND';
            }
        """)
        
        print("Dockerfile Row HTML:")
        print(row_html[:1500])
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
