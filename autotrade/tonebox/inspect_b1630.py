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
        
        # 1. Close any open drawer first
        await target_page.keyboard.press("Escape")
        await asyncio.sleep(0.5)
        
        # 2. Hover over the cell first to reveal the card icon for B00001630
        print("Hovering over B00001630 cell at (340, 254)...")
        await target_page.mouse.move(340, 254)
        await asyncio.sleep(0.5)
        
        # 3. Click the card icon at (445, 254)
        print("Clicking card icon at (445, 254)...")
        await target_page.mouse.click(445, 254)
        await asyncio.sleep(4.0)
        
        # 4. Check if record drawer is open
        drawer_visible = await target_page.evaluate("""
            () => {
                const card = document.querySelector('.base-record-card, [class*="record-card"]');
                if (!card) return null;
                const titleEl = card.querySelector('[class*="record-title"], [class*="RecordTitle"], h1, [class*="modal-title"]');
                return titleEl ? titleEl.innerText.trim() : 'CARD_OPEN_WITHOUT_TITLE';
            }
        """)
        print("Is record drawer open?", drawer_visible)
        
        # 5. Scroll and dump all fields
        all_fields = {}
        for scroll_top in [0, 300, 600, 900, 1200]:
            await target_page.evaluate(f"""
                () => {{
                    const container = document.querySelector('.bitable-record-page-content');
                    if (container) {{
                        container.scrollTop = {scroll_top};
                    }}
                }}
            """)
            await asyncio.sleep(0.5)
            
            fields_step = await target_page.evaluate("""
                () => {
                    const results = [];
                    const items = document.querySelectorAll('.bitable-record-card-field-wrapper, .bitable-field-item, .b-field-label');
                    items.forEach(item => {
                        const labelEl = item.querySelector('.bitable-field-name, [class*="field-name"], [class*="field-label"]');
                        if (!labelEl) return;
                        const label = labelEl.innerText.trim();
                        
                        const valueEl = item.querySelector('.b-field-label__card_editor, .b-field-label__editor, [class*="value"], [class*="cell"], [class*="editor"]');
                        const value = valueEl ? valueEl.innerText.trim() : '';
                        
                        results.push({ label, value });
                    });
                    return results;
                }
            """)
            
            for f in fields_step:
                if f['label']:
                    lbl_clean = f['label'].replace('\u200b', '').strip()
                    all_fields[lbl_clean] = f['value']
                    
        print(f"\nFields in B00001630:")
        for idx, (label, val) in enumerate(sorted(all_fields.items())):
            print(f"  Field: '{label}' -> '{val.replace(chr(10), ' | ')[:150]}'")
            
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/check_b1630_opened.png")
        print("Saved check_b1630_opened.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
