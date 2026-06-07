import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        # Find target page (Lark page)
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
            
        print(f"Target page: {await target_page.title()} ({target_page.url})")
        await target_page.bring_to_front()
        await asyncio.sleep(2)
        
        # Check if Back to Edit is visible
        text = await target_page.evaluate("() => document.body.innerText")
        if "Back to Edit" in text:
            print("Clicking 'Back to Edit'...")
            back_btn = target_page.locator("button:has-text('Back to Edit'), [class*='btn']:has-text('Back to Edit')").first
            await back_btn.click(force=True)
            await asyncio.sleep(2)
            
        # Click "+ Add Record" button
        print("Locating + Add Record button...")
        add_btn = target_page.locator("text=Add Record, button:has-text('Add Record'), [class*='add-record'], .bitable-append-records-btn-wrapper button").first
        print("Clicking + Add Record button...")
        await add_btn.click(force=True)
        await asyncio.sleep(5)
        
        # Take a screenshot to see if the drawer is open
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/after_add_clicked.png", timeout=5000)
        print("Screenshot saved to after_add_clicked.png")
        
        # Inspect HTML classes in the document to see if the drawer or modal fields are visible
        classes_info = await target_page.evaluate("""
            () => {
                const elements = Array.from(document.querySelectorAll('*'));
                const classes = new Set();
                elements.forEach(el => {
                    if (el.className && typeof el.className === 'string') {
                        el.className.split(' ').forEach(c => {
                            if (c.includes('field') || c.includes('record') || c.includes('drawer') || c.includes('card') || c.includes('detail')) {
                                classes.add(c);
                            }
                        });
                    }
                });
                return Array.from(classes);
            }
        """)
        print("Found classes relating to fields/records/drawers:")
        print(classes_info)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
