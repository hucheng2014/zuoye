import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        page = await context.new_page()
        
        url = "https://bytedance.larkoffice.com/base/B4SgbbhcyaJfwWsWHvcc1AtgnYd?table=tblcXB0RGGaHGm1r&view=vewxWP7trZ"
        print("Navigating to table...")
        await page.goto(url)
        await asyncio.sleep(8)
        
        # Click the Add Record button
        print("Clicking '+ Add Record' button...")
        add_btn = page.locator("text=Add Record, button:has-text('Add Record'), [class*='add-record']").first
        
        if await add_btn.count() > 0:
            await add_btn.click()
            print("Clicked Add Record. Waiting for modal/cell to focus...")
            await asyncio.sleep(4)
            
            # Take screenshot of the form/modal
            await page.screenshot(path="/home/jianglei/zuoye/traedocker/bbs_add_form.png")
            print("Screenshot saved to /home/jianglei/zuoye/traedocker/bbs_add_form.png")
            
            # Let's inspect the DOM elements of the opened modal/card view
            inputs = await page.evaluate("""
                () => {
                    const elements = [];
                    // Find form inputs, fields, textareas, and card elements
                    const fields = document.querySelectorAll('input, textarea, [role="button"], [class*="field"], [class*="cell"]');
                    fields.forEach(el => {
                        if (el.innerText || el.getAttribute('placeholder')) {
                            elements.push({
                                tagName: el.tagName,
                                className: el.className,
                                text: el.innerText ? el.innerText.trim().substring(0, 100) : '',
                                placeholder: el.getAttribute('placeholder') || ''
                            });
                        }
                    });
                    return elements.slice(0, 80);
                }
            """)
            print("Fields found in the view:")
            for idx, inp in enumerate(inputs):
                if inp['text'] or inp['placeholder']:
                    print(f"[{idx}] Tag: {inp['tagName']}, Class: {inp['className'][:40]}, Text: {inp['text'][:50]}, Placeholder: {inp['placeholder']}")
        else:
            print("Add Record button not found!")
            
        await page.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
