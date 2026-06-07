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
        
        print("Reloading page...")
        await target_page.reload()
        await asyncio.sleep(8)
        
        # Locate the main table grid canvas
        # Typically the table content wrapper has class 'bitable-table-view--content' or contains canvas
        canvas = target_page.locator(".bitable-table-view--content canvas").first
        if await canvas.count() == 0:
            canvas = target_page.locator("canvas").first
            
        box = await canvas.bounding_box()
        if not box:
            print("Grid canvas not found!")
            await browser.close()
            return
            
        print(f"Main grid canvas box: {box}")
        
        # Row 1 is usually header, Row 2 is B00001573, Row 3 is B00001626
        # Let's right click on Row 3 (the B00001626 row)
        # Header is y=0 to y=32. Row 2 (B00001573) is y=32 to y=64. Row 3 (B00001626) is y=64 to y=96.
        # Let's click at y = 80 relative to canvas (middle of Row 3) and x = 150
        click_x = box['x'] + 150
        click_y = box['y'] + 80
        print(f"Right-clicking at x={click_x}, y={click_y}")
        
        await target_page.mouse.click(click_x, click_y, button="right")
        await asyncio.sleep(2)
        
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/right_click_menu.png")
        print("Saved screenshot to right_click_menu.png")
        
        # Print elements of any visible menu
        menu_info = await target_page.evaluate("""
            () => {
                const list = [];
                const menus = document.querySelectorAll('.ud__menu, [class*="menu"], [class*="context-menu"]');
                menus.forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        list.push({
                            className: el.className,
                            text: el.innerText.trim()
                        });
                    }
                });
                return list;
            }
        """)
        print("Visible menus:", menu_info)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
