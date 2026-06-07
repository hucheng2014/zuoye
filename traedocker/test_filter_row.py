import asyncio
import re
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
        
        # Click Add Record
        print("Clicking Add Record...")
        add_btn = target_page.locator('[data-e2e="bitable-add-record-btn"], .bitable-append-records-btn-wrapper button').first
        await add_btn.click(force=True)
        await asyncio.sleep(4)
        
        # Try to locate row using regex filter
        async def get_row(field_name):
            row = target_page.locator(".base_record_card_field_editor_wrapper, .bitable-node-container-wrapper-field").filter(
                has=target_page.locator(".bitable-field-name, [class*='field-name'], [class*='field-label']").filter(
                    has_text=re.compile(f"^{field_name}$")
                )
            ).first
            return row
            
        row = await get_row("父记录")
        print(f"Row count for '父记录': {await row.count()}")
        if await row.count() > 0:
            print("Row HTML snippet:")
            print(await row.evaluate("el => el.outerHTML.substring(0, 300)"))
            
            # Click trigger
            print("Clicking trigger...")
            await row.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button']").first.click(force=True)
            await asyncio.sleep(2)
            
            # Save screenshot
            await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/parent_selection_filter.png")
            print("Saved screenshot to parent_selection_filter.png")
            
            await target_page.keyboard.press("Escape")
            await asyncio.sleep(1)
            
        # Close drawer
        close_btn = target_page.locator("button:has-text('Exit'), button:has-text('取消'), [class*='exit']").first
        if await close_btn.count() > 0:
            await close_btn.click(force=True)
            await asyncio.sleep(2)
            
        # Dismiss warning popup
        back_btn = target_page.locator("button:has-text('Exit'), [class*='btn']:has-text('Exit')").first
        if await back_btn.count() > 0:
            await back_btn.click(force=True)
            await asyncio.sleep(2)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
