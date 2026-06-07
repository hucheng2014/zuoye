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
        
        # The context menu is still open. We need to find the specific menu items.
        # Let's get all visible menu items with their text
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/menu_open.png")
        
        # Look at what's visible in the menu area (y=370-650 based on screenshot)
        # The menu items are li elements or div elements inside the b-menu
        menu_texts = await target_page.evaluate("""
            () => {
                const results = [];
                // Find items inside the b-menu div
                const menu = document.querySelector('.b-menu');
                if (!menu) return [{error: 'No .b-menu found'}];
                
                const allChildren = menu.querySelectorAll('*');
                allChildren.forEach((el, idx) => {
                    const rect = el.getBoundingClientRect();
                    if (rect.height > 0 && rect.height < 45 && rect.width > 50) {
                        const text = (el.innerText || el.textContent || '').trim();
                        if (text && text.length < 60) {
                            results.push({
                                idx,
                                tag: el.tagName,
                                text,
                                x: Math.round(rect.x + rect.width/2),
                                y: Math.round(rect.y + rect.height/2),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            });
                        }
                    }
                });
                return results;
            }
        """)
        
        print(f"Menu items ({len(menu_texts)}):")
        for item in menu_texts:
            if 'error' in item:
                print(f"  ERROR: {item}")
            else:
                print(f"  [{item['idx']}] <{item['tag']}> '{item['text']}' at ({item['x']}, {item['y']}) {item['width']}x{item['height']}")
        
        # Find "Add Sub-record"
        target = None
        for item in menu_texts:
            if 'error' not in item:
                t = item['text']
                if 'Sub' in t or 'sub' in t.lower() or '子' in t:
                    target = item
                    break
        
        if target:
            print(f"\nClicking 'Add Sub-record' at ({target['x']}, {target['y']})...")
            await target_page.mouse.click(target['x'], target['y'])
            await asyncio.sleep(3)
            await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/after_add_sub_record.png")
            print("Saved after_add_sub_record.png")
            
            # Check if a new form/drawer opened
            new_record_form = await target_page.evaluate("""
                () => {
                    const form = document.querySelector('.base-record-card, [class*="add-record"], [class*="record-form"]');
                    return form ? {found: true, text: (form.innerText || '').substring(0, 200)} : {found: false};
                }
            """)
            print(f"New record form: {new_record_form}")
        else:
            print("\n'Add Sub-record' not found in menu")
            # Close menu
            await target_page.keyboard.press("Escape")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
