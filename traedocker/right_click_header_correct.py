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
        
        # 1. Reset sidebar view
        await target_page.mouse.click(60, 125)
        await asyncio.sleep(2)
        
        # Clear search clear if visible
        search_clear = target_page.locator(".ud__input-search-clear, [class*='clear']").first
        if await search_clear.count() > 0 and await search_clear.is_visible():
            await search_clear.click(force=True)
            await asyncio.sleep(1)
            
        # 2. Right click on the row header of B00001886 (x=255, y=458)
        print("Right-clicking row header at x=255, y=458...")
        await target_page.mouse.click(255, 458, button="right")
        await asyncio.sleep(2)
        
        # Check visible menu text
        menu_items = await target_page.evaluate("""
            () => {
                const list = [];
                const items = document.querySelectorAll('.ud__menu-item, [class*="menu-item"], [role="menuitem"], .bitable-context-menu-item');
                items.forEach((el, index) => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        const txt = el.innerText || el.textContent || "";
                        list.push({
                            index: index,
                            text: txt.trim(),
                            x: rect.x + rect.width / 2,
                            y: rect.y + rect.height / 2
                        });
                    }
                });
                return list;
            }
        """)
        
        print("Menu items found:")
        for item in menu_items:
            print(f"[{item['index']}] Text: {item['text']} at ({item['x']}, {item['y']})")
            
        # Look for "展开记录" or "展开" or "Open"
        target_item = None
        for item in menu_items:
            t = item['text']
            if "展开记录" in t or "展开" in t or "Open" in t or "Expand" in t:
                target_item = item
                break
                
        if target_item:
            print(f"Clicking menu item '{target_item['text']}' at ({target_item['x']}, {target_item['y']})...")
            await target_page.mouse.click(target_item['x'], target_item['y'])
            await asyncio.sleep(4)
            
            # Check if record details card is open
            drawer_visible = await target_page.evaluate("""
                () => !!document.querySelector('.base-record-card, [class*="record-card"]');
            """)
            print("Is record details card open?", drawer_visible)
            
            # Save screenshot
            await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/after_right_click_header_correct.png")
            print("Saved after_right_click_header_correct.png")
        else:
            print("Open menu item not found!")
            await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/right_click_header_failed.png")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
