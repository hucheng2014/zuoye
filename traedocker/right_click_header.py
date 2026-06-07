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
        
        # Click sidebar tab to reset
        await target_page.mouse.click(60, 125)
        await asyncio.sleep(2)
        
        # Right click on the row header (x=135, y=458)
        print("Right-clicking row header...")
        await target_page.mouse.click(135, 458, button="right")
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
            
        # Capture screenshot
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/right_click_header.png")
        print("Saved right_click_header.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
