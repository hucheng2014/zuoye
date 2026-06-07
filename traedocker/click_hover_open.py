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
        
        # 1. Click sidebar grid tab
        await target_page.mouse.click(60, 125)
        await asyncio.sleep(2)
        
        # 2. Click cell to select it and trigger hover icon
        print("Selecting cell B00001886...")
        await target_page.mouse.click(230, 458)
        await asyncio.sleep(1)
        
        # 3. Click the open icon which is at the right edge of the cell (x=278, y=458)
        print("Clicking Open icon inside cell...")
        await target_page.mouse.click(278, 458)
        await asyncio.sleep(4)
        
        # Check if details drawer is open
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        print("Is record details card open?", drawer_visible)
        
        # Take a screenshot
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/after_icon_click.png")
        print("Saved after_icon_click.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
