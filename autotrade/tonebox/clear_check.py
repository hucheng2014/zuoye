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
        
        # 1. Close any open drawer
        await target_page.keyboard.press("Escape")
        await asyncio.sleep(0.5)
        
        # 2. Clear search box if visible
        search_clear = target_page.locator(".ud__input-search-clear, [class*='clear']").first
        if await search_clear.count() > 0 and await search_clear.is_visible():
            print("Clearing existing search...")
            await search_clear.click(force=True)
            await asyncio.sleep(2.0)
            
        # 3. Take screenshot
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/clear_check.png")
        print("Saved clear_check.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
