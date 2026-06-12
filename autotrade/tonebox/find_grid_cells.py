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
        
        # Ensure search is cleared
        search_clear = target_page.locator(".ud__input-search-clear, [class*='clear']").first
        if await search_clear.count() > 0 and await search_clear.is_visible():
            await search_clear.click(force=True)
            await asyncio.sleep(1)
            
        # Get canvas box
        canvas = target_page.locator(".bitable-table-view--content canvas, canvas").first
        box = await canvas.bounding_box()
        if not box:
            print("Canvas not found!")
            await browser.close()
            return
        print(f"Canvas box: {box}")
        
        # We will try clicking at y = 458 (which should be Row 9 unfiltered)
        # and different x coordinates to find the columns.
        y_coord = box['y'] + 310 # y = 458 if box['y'] is 148
        print(f"Testing clicks at y={y_coord}...")
        
        for x_offset in range(50, 400, 40):
            x_coord = box['x'] + x_offset
            print(f"Clicking at x={x_coord} (offset {x_offset})...")
            await target_page.mouse.click(x_coord, y_coord)
            await asyncio.sleep(0.5)
            
            # Check selection cursor
            cursor_box = await target_page.evaluate("""
                () => {
                    const cursor = document.querySelector('.selection-cursor');
                    if (cursor) {
                        const r = cursor.getBoundingClientRect();
                        return { x: r.x, y: r.y, width: r.width, height: r.height };
                    }
                    return null;
                }
            """)
            if cursor_box:
                print(f"  -> Selection cursor found: {cursor_box}")
                # Try pressing Space to see if it opens the record
                await target_page.keyboard.press("Space")
                await asyncio.sleep(2.5)
                
                drawer_visible = await target_page.evaluate("""
                    () => !!document.querySelector('.base-record-card, [class*="record-card"]');
                """)
                if drawer_visible:
                    print(f"  -> SUCCESS! Record opened at x_offset={x_offset}")
                    await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/record_opened_success.png")
                    break
                else:
                    print("  -> Record drawer did not open.")
            else:
                print("  -> No selection cursor.")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
