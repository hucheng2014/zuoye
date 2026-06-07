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
        
        # Detect new elements added when we click the select trigger
        new_elements = await page.evaluate("""
            async () => {
                const before = new Set(Array.from(document.querySelectorAll('*')));
                
                // Helper to get field wrapper
                const getFieldWrapper = (labelText) => {
                    const names = Array.from(document.querySelectorAll('.bitable-field-name'));
                    const targetName = names.find(n => n.innerText.trim() === labelText);
                    if (targetName) {
                        let parent = targetName;
                        while (parent && !parent.className.includes('base_record_card_field_editor_wrapper')) {
                            parent = parent.parentElement;
                        }
                        return parent;
                    }
                    return null;
                };
                
                const wrapper = getFieldWrapper('repo_type');
                if (wrapper) {
                    // Click on the 'Please select' text
                    const selectEl = Array.from(wrapper.querySelectorAll('*')).find(el => el.innerText && el.innerText.trim() === 'Please select');
                    if (selectEl) {
                        selectEl.click();
                        console.log("Clicked 'Please select' element");
                    } else {
                        console.log("'Please select' element not found in wrapper");
                    }
                } else {
                    console.log("Wrapper for 'repo_type' not found");
                }
                
                // Wait for animation
                await new Promise(resolve => setTimeout(resolve, 1500));
                
                // Diff the elements
                const after = Array.from(document.querySelectorAll('*'));
                const diff = after.filter(el => !before.has(el));
                
                return diff.map(el => ({
                    tagName: el.tagName,
                    className: el.className,
                    innerText: el.innerText ? el.innerText.trim() : ''
                })).filter(item => item.innerText.length > 0 && item.innerText.length < 100);
            }
        """)
        
        print("New elements added to DOM after clicking:")
        seen_texts = set()
        for idx, el in enumerate(new_elements):
            if el['innerText'] not in seen_texts:
                print(f"[{idx}] Tag: {el['tagName']}, Class: {el['className'][:50]}, Text: {el['innerText']}")
                seen_texts.add(el['innerText'])
                
        await page.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
