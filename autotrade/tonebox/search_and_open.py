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
        
        # 1. Clear search box if visible
        search_clear = target_page.locator(".ud__input-search-clear, [class*='clear']").first
        if await search_clear.count() > 0 and await search_clear.is_visible():
            await search_clear.click(force=True)
            await asyncio.sleep(1)
            
        # 2. Click Search Box and type B00001886
        search_box = target_page.locator("input[placeholder*='Search'], input[placeholder*='搜索']").first
        await search_box.click(force=True)
        await asyncio.sleep(0.5)
        await target_page.keyboard.press("Control+A")
        await target_page.keyboard.press("Backspace")
        await target_page.keyboard.type("B00001886")
        await asyncio.sleep(4)
        
        # Take screenshot of filtered result
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/search_result_b00001886.png")
        print("Saved search_result_b00001886.png")
        
        # 3. Locate the main canvas
        canvas = target_page.locator(".bitable-table-view--content canvas, canvas").first
        box = await canvas.bounding_box()
        if not box:
            print("Canvas box not found!")
            await browser.close()
            return
            
        print(f"Canvas bounding box: {box}")
        
        # Double click the first row of the grid.
        # When filtered, B00001886 should be the only row.
        # The row starts after header (approx y = 32 relative to canvas).
        # Let's click at relative x = 200, y = 50 (middle of the first row cell).
        click_x = box['x'] + 200
        click_y = box['y'] + 50
        print(f"Double-clicking cell at screen coords: x={click_x}, y={click_y}")
        await target_page.mouse.dblclick(click_x, click_y)
        await asyncio.sleep(4)
        
        # Check if record details card is open
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        print("Is record details card open?", drawer_visible)
        
        # Take a screenshot
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/record_card_search_open.png")
        print("Saved record_card_search_open.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
