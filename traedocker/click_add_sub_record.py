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
        
        # Take screenshot first
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/current_state.png")
        print("Saved current_state.png")
        
        # Check if there's a context menu open
        menu_items = await target_page.evaluate("""
            () => {
                const results = [];
                document.querySelectorAll('[class*="menu-item"], [class*="MenuItem"], [class*="context"]').forEach((el) => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        results.push({
                            text: (el.innerText || el.textContent || '').trim().substring(0, 100),
                            x: rect.x + rect.width/2,
                            y: rect.y + rect.height/2,
                            className: (typeof el.className === 'string' ? el.className : 'SVGClass').substring(0, 60)
                        });
                    }
                });
                return results;
            }
        """)
        
        print(f"Context menu items ({len(menu_items)}):")
        for item in menu_items:
            print(f"  '{item['text']}' at ({item['x']:.0f}, {item['y']:.0f}) class: {item['className']}")
        
        # Look for "Add Sub-record" button
        add_sub_record = None
        for item in menu_items:
            if 'sub' in item['text'].lower() or 'Sub' in item['text'] or '子' in item['text']:
                add_sub_record = item
                break
        
        if add_sub_record:
            print(f"\nFound 'Add Sub-record' at ({add_sub_record['x']:.0f}, {add_sub_record['y']:.0f})")
            await target_page.mouse.click(add_sub_record['x'], add_sub_record['y'])
            await asyncio.sleep(3)
            print("Clicked 'Add Sub-record'")
            await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/after_add_sub.png")
            print("Saved after_add_sub.png")
        else:
            print("Menu is not open or 'Add Sub-record' not found")
            # Close any open menus and re-trigger on B00001886
            await target_page.keyboard.press("Escape")
            await asyncio.sleep(1)
            
            # Look for the last row (B00001886) by finding where it appears in the grid
            # Canvas starts at y=148, row height is about 25px based on the screenshots
            # Let me try to find the row by looking for the specific text
            # B00001886 is the last row at y ≈ 360 in the screenshot with rows at:
            # Header: 148-172, rows are ~25px each
            # So row positions (center): 184.5, 209.5, 234.5, 259.5, 284.5, 309.5, 334.5, 359.5
            # Row 9 = B00001886: center at y=360
            
            # Right-click at that position
            print("Attempting right-click at B00001886 row (y=360)...")
            await target_page.mouse.click(340, 361, button="right")
            await asyncio.sleep(2)
            
            await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/rc_b1886.png")
            
            # Now look for Add Sub-record again
            menu_items2 = await target_page.evaluate("""
                () => {
                    const results = [];
                    document.querySelectorAll('[class*="menu-item"], [class*="MenuItem"]').forEach((el) => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            results.push({
                                text: (el.innerText || el.textContent || '').trim().substring(0, 100),
                                x: rect.x + rect.width/2,
                                y: rect.y + rect.height/2,
                            });
                        }
                    });
                    return results;
                }
            """)
            
            print(f"Context menu items (2nd attempt, {len(menu_items2)}):")
            for item in menu_items2:
                print(f"  '{item['text']}' at ({item['x']:.0f}, {item['y']:.0f})")
            
            for item in menu_items2:
                if 'sub' in item['text'].lower() or 'Sub' in item['text'] or '子' in item['text']:
                    print(f"Found 'Add Sub-record' at ({item['x']:.0f}, {item['y']:.0f})")
                    await target_page.mouse.click(item['x'], item['y'])
                    await asyncio.sleep(3)
                    await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/after_add_sub2.png")
                    break
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
