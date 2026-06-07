import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        target_page = None
        for idx, page in enumerate(context.pages):
            title = await page.title()
            if "需求二正式作业表_BBS" in title and not title.startswith("\u202d"):
                target_page = page
                print(f"Selected Page [{idx}]: {title}")
                break
                
        if not target_page:
            target_page = context.pages[0]
            print(f"Fallback to Page [0]: {await target_page.title()}")
            
        await target_page.bring_to_front()
        await asyncio.sleep(1)
        
        # Check if drawer is open
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        print(f"Drawer visible? {drawer_visible}")
        if not drawer_visible:
            print("Opening drawer...")
            await target_page.locator('[data-e2e="bitable-add-record-btn"]').first.click(force=True)
            await asyncio.sleep(3)
            
        # Get repo_type row
        row = target_page.locator(".base_record_card_field_editor_wrapper, .bitable-field-item").filter(
            has=target_page.locator(".bitable-field-name, [class*='field-name']", has_text="repo_type")
        ).first
        
        # Click dropdown trigger
        print("Clicking dropdown trigger...")
        await row.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button']").first.click(force=True)
        await asyncio.sleep(2)
        
        # Capture screenshot when dropdown is open
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/select_clicked.png")
        print("Screenshot saved to select_clicked.png")
        
        # Inspect overlay HTML
        overlay_htmls = await target_page.evaluate("""
            () => {
                const results = [];
                // Look for elements with high z-index or absolute positions typical of dropdown overlays
                const elements = document.querySelectorAll('.ud__select-menu, [role="listbox"], .ud__dropdown, .ud__dropdown-menu, [class*="select-menu"], [class*="dropdown-menu"]');
                elements.forEach((el, idx) => {
                    results.push({
                        idx,
                        tagName: el.tagName,
                        className: el.className,
                        html: el.outerHTML.substring(0, 1000)
                    });
                });
                return results;
            }
        """)
        
        print(f"Dropdown overlays found: {len(overlay_htmls)}")
        for overlay in overlay_htmls:
            print(f"Overlay [{overlay['idx']}] Tag: {overlay['tagName']}, Class: {overlay['className']}")
            print(overlay['html'])
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
