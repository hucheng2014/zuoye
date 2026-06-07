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
        
        # Clear search box first so we can see the grid clearly
        search_close = target_page.locator(".ud__input-search-clear, [class*='clear']").first
        if await search_close.count() > 0 and await search_close.is_visible():
            await search_close.click(force=True)
            await asyncio.sleep(1)
            
        # We need to scroll the grid horizontally to see other columns.
        # In Lark Base, the scrollbar or the grid container can be scrolled.
        # Let's locate the canvas or grid viewport.
        # We can simulate pressing arrow keys (Right) multiple times to scroll the grid.
        # First, click on a cell to focus the grid (e.g. click at coordinate where B00001573 is, say x=180, y=200)
        await target_page.mouse.click(180, 200)
        await asyncio.sleep(1)
        
        # Press Right arrow multiple times to scroll right
        for _ in range(15):
            await target_page.keyboard.press("ArrowRight")
            await asyncio.sleep(0.1)
            
        await asyncio.sleep(2)
        
        # Take a screenshot
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/scrolled_view.png")
        print("Saved scrolled_view.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
