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
        
        # 1. Reset sidebar view
        await target_page.mouse.click(60, 125)
        await asyncio.sleep(2)
        
        # Clear search clear if visible
        search_clear = target_page.locator(".ud__input-search-clear, [class*='clear']").first
        if await search_clear.count() > 0 and await search_clear.is_visible():
            await search_clear.click(force=True)
            await asyncio.sleep(1)
            
        # 2. Right click on row header (x=135, y=458)
        print("Right-clicking row header...")
        await target_page.mouse.click(135, 458, button="right")
        await asyncio.sleep(1.5)
        
        # 3. Click "Open Record" at x=225, y=670
        print("Clicking Open Record menu item...")
        await target_page.mouse.click(225, 670)
        await asyncio.sleep(4)
        
        # Check if record details card is open
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        print("Is record details card open?", drawer_visible)
        
        # Take a screenshot
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/record_card_opened.png")
        print("Saved record_card_opened.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
