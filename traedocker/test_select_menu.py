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
            
        print(f"Target page: {await target_page.title()}")
        await target_page.bring_to_front()
        
        # Click Back to Edit if visible
        back_btn = target_page.locator("button:has-text('Back to Edit'), [class*='btn']:has-text('Back to Edit')")
        if await back_btn.count() > 0:
            print("Clicking 'Back to Edit'...")
            await back_btn.first.click(force=True)
            await asyncio.sleep(2)
            
        # Find repo_type row and click dropdown trigger
        row = target_page.locator(".base_record_card_field_editor_wrapper").filter(
            has=target_page.locator(".bitable-field-name, [class*='field-name']", has_text="repo_type")
        ).first
        
        print("Clicking dropdown trigger...")
        await row.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button']").first.click(force=True)
        await asyncio.sleep(2)
        
        # Extract dropdown overlay HTML
        overlay_html = await target_page.evaluate("""
            () => {
                // Find potential select menus or dropdown listboxes
                const menus = document.querySelectorAll('.ud__select-menu, [role="listbox"], [class*="select-menu"], [class*="dropdown-menu"]');
                return Array.from(menus).map(m => m.outerHTML);
            }
        """)
        
        print(f"Dropdown overlays found: {len(overlay_html)}")
        for idx, html in enumerate(overlay_html):
            print(f"[{idx}] HTML structure:")
            print(html[:1500])
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
