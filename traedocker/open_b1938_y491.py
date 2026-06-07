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
        
        # Close the current open record
        await target_page.keyboard.press("Escape")
        await asyncio.sleep(0.5)
        
        # From analysis: B00001886 visual y=361, actual click y=465, offset=104
        # B00001938 visual y=387, actual click y=387+104=491
        
        print("Right-clicking at y=491 for B00001938...")
        await target_page.mouse.click(340, 491, button="right")
        await asyncio.sleep(2)
        
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/rc_491.png")
        print("Saved rc_491.png")
        
        # Find "Open Record" in menu
        menu = document = await target_page.evaluate("""
            () => {
                const menu = document.querySelector('.b-menu');
                if (!menu) return {found: false, text: ''};
                return {found: true, text: menu.innerText.substring(0, 300)};
            }
        """)
        print(f"Menu: {menu}")
        
        # Click "Open Record"
        open_record = target_page.locator('li:has-text("Open Record")')
        if await open_record.count() > 0 and await open_record.first.is_visible():
            print("Found 'Open Record' - clicking...")
            await open_record.first.click()
            await asyncio.sleep(3)
            
            # Check which record opened
            title = await target_page.evaluate("""
                () => {
                    const titleEl = document.querySelector('[class*="record-title"], [class*="RecordTitle"], h1, [class*="modal-title"]');
                    if (titleEl) return titleEl.innerText;
                    
                    // Look for the B000xxxxx ID in the right panel
                    const panel = document.querySelector('.base-record-card');
                    if (panel) {
                        const text = panel.innerText;
                        const match = text.match(/B\\d{8}/);
                        return match ? match[0] : text.substring(0, 100);
                    }
                    return 'No title found';
                }
            """)
            print(f"Opened record: {title}")
            
            await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/opened_491.png")
            print("Saved opened_491.png")
        else:
            print("'Open Record' not found")
            await target_page.keyboard.press("Escape")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
