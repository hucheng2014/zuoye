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
        
        # Canvas box: x=240, y=148, width=1671, height=840
        # Row height in Lark Base grid is typically 32-36 pixels
        # Header row: y=148 to y=180 (32px)
        # Row 1 (B00001573): y=180 to y=212
        # Row 2 (B00001629): y=212 to y=244
        # Sub-rows: 3..9 (B00001630..B00001886)
        # Row 3 (B00001630): y=244 to y=276
        # Row 4 (B00001631): y=276 to y=308
        # Row 5 (B00001632): y=308 to y=340
        # Row 6 (B00001633): y=340 to y=372 -- this was the row I was clicking!
        # Row 7 (B00001634): y=372 to y=404
        # Row 8 (B00001635): y=404 to y=436
        # Row 9 (B00001886): y=436 to y=468
        
        # So B00001886 is at y=436 to y=468, center at y=452
        # Let me try clicking at y=452 which is in the B00001886 row
        
        # First verify by right-clicking and checking context menu
        print("Right-clicking at y=452 to check row...")
        await target_page.mouse.click(340, 452, button="right")
        await asyncio.sleep(2)
        
        # Check visible context menu items
        menu_items = await target_page.evaluate("""
            () => {
                const results = [];
                document.querySelectorAll('.ud__menu-item, [class*="menu-item"], [role="menuitem"], [class*="context-menu"]').forEach((el, idx) => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        results.push({
                            idx,
                            text: (el.innerText || el.textContent || '').trim(),
                            x: rect.x + rect.width/2,
                            y: rect.y + rect.height/2,
                            class: el.className.substring(0, 60)
                        });
                    }
                });
                return results;
            }
        """)
        
        print(f"Context menu items ({len(menu_items)}):")
        for item in menu_items:
            print(f"  [{item['idx']}] '{item['text']}' at ({item['x']:.0f}, {item['y']:.0f})")
        
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/rightclick_452.png")
        print("Saved rightclick_452.png")
        
        # Look for "Insert" child or "Add child" or "展开记录" (Open Record)  
        target_item = None
        for item in menu_items:
            t = item['text'].lower()
            if '子' in item['text'] or 'child' in t or '插入' in item['text'] or '展开' in item['text'] or 'open' in t or 'expand' in t:
                target_item = item
                break
                
        if target_item:
            print(f"Found target menu item: '{target_item['text']}' at ({target_item['x']}, {target_item['y']})")
            await target_page.mouse.click(target_item['x'], target_item['y'])
            await asyncio.sleep(3)
            
            await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/after_menu_click.png")
        else:
            print("No 'Open/Child/Expand' menu item found!")
            # Close the menu
            await target_page.keyboard.press("Escape")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
