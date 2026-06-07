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
        
        # Close any open drawer first
        await target_page.keyboard.press("Escape")
        await asyncio.sleep(0.5)
        
        # Double click B00001938 cell at (340, 491)
        print("Double-clicking cell at (340, 491)...")
        await target_page.mouse.dblclick(340, 491)
        await asyncio.sleep(4.0)
        
        # Check if record details card is open
        drawer_visible = await target_page.evaluate("""
            () => {
                const card = document.querySelector('.base-record-card, [class*="record-card"]');
                if (!card) return false;
                const titleEl = card.querySelector('[class*="record-title"], [class*="RecordTitle"], h1, [class*="modal-title"]');
                return titleEl ? titleEl.innerText.trim() : 'CARD_OPEN_WITHOUT_TITLE';
            }
        """)
        print("Is record details card open?", drawer_visible)
        
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/check_dblclick_491.png")
        print("Saved check_dblclick_491.png")
        
        # If not open, try right-click menu navigation
        if not drawer_visible:
            print("Double-click did not open drawer. Trying right-click menu at (340, 491)...")
            await target_page.mouse.click(340, 491, button="right")
            await asyncio.sleep(2.0)
            
            # Look for menu items
            menu_info = await target_page.evaluate("""
                () => {
                    const menu = document.querySelector('.b-menu, [class*="menu"]');
                    if (!menu) return null;
                    return menu.innerText;
                }
            """)
            print(f"Context menu visible: {menu_info is not None}")
            if menu_info:
                print(f"Menu text:\n{menu_info}")
                
            # Click Open Record / 打开记录
            open_item = target_page.locator('.ud__menu-item:has-text("Open Record"), [class*="menu-item"]:has-text("Open Record"), .ud__menu-item:has-text("打开记录"), [class*="menu-item"]:has-text("打开记录")').first
            if await open_item.count() > 0:
                print("Clicking Open Record menu item...")
                await open_item.click()
                await asyncio.sleep(4.0)
                
                drawer_visible = await target_page.evaluate("""
                    () => {
                        const card = document.querySelector('.base-record-card, [class*="record-card"]');
                        if (!card) return false;
                        const titleEl = card.querySelector('[class*="record-title"], [class*="RecordTitle"], h1, [class*="modal-title"]');
                        return titleEl ? titleEl.innerText.trim() : 'CARD_OPEN_WITHOUT_TITLE';
                    }
                """)
                print("Is record details card open after right-click?", drawer_visible)
                await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/check_rightclick_491.png")
                print("Saved check_rightclick_491.png")
            else:
                print("Open record item not found in context menu.")
                await target_page.keyboard.press("Escape")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
