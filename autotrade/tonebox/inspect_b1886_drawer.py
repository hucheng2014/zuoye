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
        
        # Check if drawer is open
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        print(f"Drawer visible: {drawer_visible}")
        
        if not drawer_visible:
            print("Opening B00001886 drawer...")
            # Click at x=530, y=458 to select the row (x_offset=290 worked)
            await target_page.mouse.click(530, 360)
            await asyncio.sleep(0.5)
            await target_page.keyboard.press("Space")
            await asyncio.sleep(3)
        
        # Scroll down in the drawer to see all fields
        drawer = target_page.locator(".base-record-card, [class*='record-card']").first
        await drawer.evaluate("el => el.scrollTop = 600")
        await asyncio.sleep(1)
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/drawer_scrolled_1.png")
        print("Saved drawer_scrolled_1.png")
        
        await drawer.evaluate("el => el.scrollTop = 1200")
        await asyncio.sleep(1)
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/drawer_scrolled_2.png")
        print("Saved drawer_scrolled_2.png")
        
        # Get all field names
        fields_info = await target_page.evaluate("""
            () => {
                const results = [];
                const items = document.querySelectorAll('.base_record_card_field_editor_wrapper, .bitable-field-item');
                items.forEach((item, idx) => {
                    const labelEl = item.querySelector('.bitable-field-name, [class*="field-name"], [class*="field-label"]');
                    const label = labelEl ? labelEl.innerText.trim() : 'NO_LABEL';
                    
                    const inputEl = item.querySelector('input, textarea');
                    let val = '';
                    if (inputEl) {
                        val = inputEl.value;
                    } else {
                        const textEl = item.querySelector('[class*="value"], [class*="text"], [class*="cell"]');
                        if (textEl) {
                            val = textEl.innerText.trim();
                        }
                    }
                    results.push({ idx, label, val: val.substring(0, 150) });
                });
                return results;
            }
        """)
        
        print(f"Drawer fields ({len(fields_info)} total):")
        for field in fields_info:
            print(f"Field [{field['idx']}] Label: '{field['label']}', Value: '{field['val']}'")
            
        # Look for a "Add Child Record" / "新增子记录" button
        child_btns = await target_page.evaluate("""
            () => {
                const results = [];
                document.querySelectorAll('button, [role="button"], a').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    const text = el.innerText || el.textContent || '';
                    if (rect.width > 0 && rect.height > 0 && 
                        (text.includes('子') || text.includes('child') || text.includes('Child') || text.includes('Add') || text.includes('新增'))) {
                        results.push({
                            text: text.trim(),
                            x: rect.x + rect.width/2,
                            y: rect.y + rect.height/2,
                            class: el.className
                        });
                    }
                });
                return results;
            }
        """)
        
        print("\nButtons with child/add text:")
        for btn in child_btns:
            print(f"  Text: '{btn['text']}', Coords: ({btn['x']}, {btn['y']}), Class: {btn['class'][:50]}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
