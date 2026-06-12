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
        
        # Check if drawer is visible
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        if not drawer_visible:
            print("Drawer not open!")
            await browser.close()
            return
            
        # Get drawer element
        drawer = target_page.locator(".base-record-card, [class*='record-card']").first
        
        # Scroll and collect
        all_fields = {}
        for scroll_top in range(0, 4000, 400):
            await drawer.evaluate(f"el => el.scrollTop = {scroll_top}")
            await asyncio.sleep(0.5)
            
            # Save screenshots at different scroll points to manually verify
            if scroll_top in [1200, 2000, 2800]:
                await target_page.screenshot(path=f"/Users/xaa/zuoye/traedocker/drawer_scroll_{scroll_top}.png")
                print(f"Saved drawer_scroll_{scroll_top}.png")
            
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
                    # Clean the label (remove ZWSP)
                    lbl_clean = f['label'].replace('\u200b', '').strip()
                    all_fields[lbl_clean] = f['value']
                    
        print(f"\nFound {len(all_fields)} unique fields in the drawer:")
        for idx, (label, val) in enumerate(sorted(all_fields.items())):
            print(f"  [{idx}] Field: '{label}' -> '{val.replace(chr(10), ' | ')[:150]}'")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
