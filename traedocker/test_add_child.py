import asyncio
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
        
        # Click + Add Record button to open a new record
        print("Clicking Add Record...")
        add_btn = target_page.locator('[data-e2e="bitable-add-record-btn"], .bitable-append-records-btn-wrapper button').first
        await add_btn.click(force=True)
        await asyncio.sleep(4)
        
        # Helper to find row
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
                    text_clean = text.replace('\u200b', '').strip().split('\n')[0]
                    if text_clean == field_name:
                        return row
            return None

        # Locate '父记录' row
        row = await get_row("父记录")
        if row:
            print("Found '父记录' row. Clicking editor trigger...")
            trigger = row.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button']").first
            await trigger.click(force=True)
            await asyncio.sleep(3)
            
            # Save screenshot of selection list
            await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/parent_selection.png")
            print("Saved screenshot to parent_selection.png")
            
            # Close/dismiss
            await target_page.keyboard.press("Escape")
            await asyncio.sleep(1)
        else:
            print("'父记录' row not found!")
            
        # Close the new record drawer
        print("Closing new record drawer...")
        close_btn = target_page.locator("button:has-text('Exit'), button:has-text('取消'), [class*='exit']").first
        if await close_btn.count() > 0:
            await close_btn.click(force=True)
            await asyncio.sleep(2)
            
        # Dismiss warning popup if it appeared
        back_btn = target_page.locator("button:has-text('Exit'), [class*='btn']:has-text('Exit')").first
        if await back_btn.count() > 0:
            await back_btn.click(force=True)
            await asyncio.sleep(2)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
