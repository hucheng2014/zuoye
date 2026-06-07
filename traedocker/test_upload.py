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
        
        # Check for file inputs in attachment fields
        file_inputs = await page.evaluate("""
            () => {
                const results = [];
                const names = ['dockerfile', 'repo', 'dockerfile构建成功截图'];
                
                names.forEach(name => {
                    const labelEls = Array.from(document.querySelectorAll('.bitable-field-name'));
                    const l = labelEls.find(el => el.innerText.trim() === name);
                    if (l) {
                        let wrapper = l;
                        while (wrapper && !wrapper.className.includes('base_record_card_field_editor_wrapper')) {
                            wrapper = wrapper.parentElement;
                        }
                        if (wrapper) {
                            const fileInput = wrapper.querySelector('input[type="file"]');
                            results.push({
                                field: name,
                                hasFileInput: !!fileInput,
                                inputHTML: fileInput ? fileInput.outerHTML.substring(0, 150) : 'None'
                            });
                        }
                    }
                });
                return results;
            }
        """)
        
        print("Attachment fields file inputs:")
        for r in file_inputs:
            print(f"Field: {r['field']}, HasFileInput: {r['hasFileInput']}, HTML: {r['inputHTML']}")
            
        await page.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
