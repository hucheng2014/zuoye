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
            await asyncio.sleep(1)
            
        # 3. Locate Search Box
        search_box = target_page.locator("input[placeholder*='Search'], input[placeholder*='搜索']").first
        if await search_box.count() > 0:
            print("Clicking search box...")
            await search_box.click(force=True)
            await asyncio.sleep(0.5)
            await target_page.keyboard.press("Control+A")
            await target_page.keyboard.press("Backspace")
            print("Typing 'B00001938'...")
            await target_page.keyboard.type("B00001938")
            await asyncio.sleep(5)
            
            # Take screenshot of filtered result
            await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/search_result_b1938.png")
            print("Saved search_result_b1938.png")
        else:
            print("Search box not found!")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
