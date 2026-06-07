import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        target_page = None
        for page in context.pages:
            url = page.url
            if "bytedance.larkoffice.com" in url:
                target_page = page
                break
                
        if not target_page:
            print("No Lark page found!")
            await browser.close()
            return
            
        print(f"Lark page: {await target_page.title()}")
        
        # From my analysis, there's an ~77px offset between visual position and actual click target
        # B00001938 is visually at y=387, so actual click should be at y=387+77=464
        # Let's try different y values to find where B00001938 responds to clicks
        
        # First, try clicking at various y values to see which selects B00001938
        for y_test in [430, 445, 460, 465, 470, 475]:
            await target_page.mouse.click(340, y_test)
            await asyncio.sleep(0.5)
            
            # Check which row is now selected by examining pixel color on canvas
            # or look for focused element
            focused_row = await target_page.evaluate("""
                () => {
                    // Check selection cursor
                    const cursor = document.querySelector('.selection-cursor, [class*="selection"]');
                    const highlighted = document.querySelector('[class*="highlighted-row"]');
                    return {
                        cursor: cursor ? cursor.getBoundingClientRect() : null,
                        highlighted: highlighted ? highlighted.getBoundingClientRect() : null
                    };
                }
            """)
            print(f"y={y_test}: selection cursor={focused_row}")
        
        # More direct approach: look at what's in the canvas area and find the exact rows
        # Let me try right-clicking at B00001938's y and see context menu header
        # Escape any selection first
        await target_page.keyboard.press("Escape")
        await asyncio.sleep(0.5)
        
        # Try right-click at y=465 for B00001938
        print("\nRight-clicking at y=465 for B00001938...")
        await target_page.mouse.click(340, 465, button="right")
        await asyncio.sleep(2)
        
        # Check the context menu - it should say "B00001938" in the record title
        menu_info = await target_page.evaluate("""
            () => {
                const menu = document.querySelector('.b-menu');
                if (!menu) return 'No menu';
                // Get first LI item - "Insert Above"
                const items = menu.querySelectorAll('li span');
                const texts = [];
                items.forEach(el => texts.push((el.innerText || '').trim()));
                return {text: menu.innerText.substring(0, 300), items: texts};
            }
        """)
        print(f"Context menu at y=465: {menu_info}")
        
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/rc_465.png")
        print("Saved rc_465.png")
        
        # Check if there's an "Open Record" option visible
        open_record_btn = target_page.locator('li:has-text("Open Record")')
        if await open_record_btn.count() > 0 and await open_record_btn.first.is_visible():
            print("Found 'Open Record' - clicking it!")
            await open_record_btn.first.click()
            await asyncio.sleep(3)
            await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/opened_from_menu.png")
        else:
            print("'Open Record' not found in menu")
            await target_page.keyboard.press("Escape")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
