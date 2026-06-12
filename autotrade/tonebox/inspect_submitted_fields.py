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
        await asyncio.sleep(1)
        
        fields_info = await target_page.evaluate("""
            () => {
                const results = [];
                // Look for fields in the detail panel (which has class .bitable-record-card-field-wrapper or similar)
                const items = document.querySelectorAll('.base_record_card_field_editor_wrapper, .bitable-field-item, .bitable-record-card-field-wrapper');
                items.forEach((item, idx) => {
                    const labelEl = item.querySelector('.bitable-field-name, [class*="field-name"], [class*="field-label"]');
                    const label = labelEl ? labelEl.innerText.trim() : 'NO_LABEL';
                    
                    // Get text value
                    const textEl = item.querySelector('[class*="value"], [class*="text"], [class*="cell"], [class*="content"]');
                    let val = textEl ? textEl.innerText.trim() : '';
                    
                    results.push({ idx, label, val });
                });
                return results;
            }
        """)
        
        print("Detail panel fields:")
        import json
        print(json.dumps(fields_info, indent=2, ensure_ascii=False))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
