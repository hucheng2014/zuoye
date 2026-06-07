import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        page = await context.new_page()
        
        url = "https://bytedance.larkoffice.com/base/B4SgbbhcyaJfwWsWHvcc1AtgnYd?table=tblcXB0RGGaHGm1r&view=vewxWP7trZ"
        await page.goto(url)
        await asyncio.sleep(8)
        
        # Open drawer
        await page.locator(".bitable-append-records-btn-wrapper button").first.click()
        await asyncio.sleep(4)
        
        # Extract structure using class bitable-field-item
        fields_info = await page.evaluate("""
            () => {
                const items = document.querySelectorAll('.bitable-field-item');
                return Array.from(items).map(item => {
                    // Try to get label text
                    const labelEl = item.querySelector('[class*="label"], [class*="title"]');
                    const label = labelEl ? labelEl.innerText.trim() : '';
                    
                    // Find input, textarea, and attachment buttons
                    const inputs = Array.from(item.querySelectorAll('input, textarea, button, [class*="select"], [class*="cell"], [class*="upload"], [class*="attachment"]')).map(el => ({
                        tagName: el.tagName,
                        className: el.className,
                        placeholder: el.placeholder || el.getAttribute('placeholder') || '',
                        innerText: el.innerText ? el.innerText.trim().substring(0, 50) : '',
                        type: el.getAttribute('type') || ''
                    }));
                    return { label, inputs };
                });
            }
        """)
        
        print("Fields and their children:")
        for idx, item in enumerate(fields_info):
            print(f"[{idx}] Label: {item['label']}")
            for j, c in enumerate(item['inputs']):
                print(f"    -> Child [{j}] Tag: {c['tagName']}, Class: {item['inputs'][j]['className'][:45]}, Text: {item['inputs'][j]['innerText']}, Type: {item['inputs'][j]['type']}, Placeholder: {item['inputs'][j]['placeholder']}")
                
        await page.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
