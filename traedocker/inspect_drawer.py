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
        
        # Click Add Record button to open the drawer
        print("Opening drawer...")
        await page.locator(".bitable-append-records-btn-wrapper button").first.click()
        await asyncio.sleep(4)
        
        # Inspect drawer DOM
        drawer_elements = await page.evaluate("""
            () => {
                const results = [];
                // The drawer container is usually a modal or sidebar on the right
                // Let's find elements that look like field containers inside the drawer
                const fields = document.querySelectorAll('[class*="field-row"], [class*="detail-item"], [class*="form-item"], [class*="row"]');
                fields.forEach(el => {
                    const label = el.querySelector('[class*="label"], [class*="title"], [class*="name"]')?.innerText || '';
                    const hasInput = el.querySelector('input') ? 'input' : '';
                    const hasTextarea = el.querySelector('textarea') ? 'textarea' : '';
                    const hasSelect = el.querySelector('[class*="select"]') ? 'select' : '';
                    const hasUpload = el.querySelector('[class*="upload"], [class*="attachment"]') ? 'upload' : '';
                    
                    if (label) {
                        results.push({
                            label: label.trim(),
                            className: el.className,
                            hasInput, hasTextarea, hasSelect, hasUpload,
                            outerHTML: el.outerHTML.substring(0, 200)
                        });
                    }
                });
                return results;
            }
        """)
        
        print("Drawer field rows found:")
        for idx, d in enumerate(drawer_elements):
            print(f"[{idx}] Label: {d['label']}")
            print(f"    Class: {d['className']}")
            print(f"    Features: Input={d['hasInput']}, Textarea={d['hasTextarea']}, Select={d['hasSelect']}, Upload={d['hasUpload']}")
            
        await page.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
