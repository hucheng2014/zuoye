import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        target_page = None
        for page in context.pages:
            title = await page.title()
            if "需求二正式作业表_BBS" in title and not title.startswith("\u202d"):
                target_page = page
                break
        if not target_page:
            target_page = context.pages[0]
            
        await target_page.bring_to_front()
        await asyncio.sleep(1)
        
        # Click close button in detail panel header
        # The selector is usually .universe-icon with data-icon="CloseOutlined" or [class*="close"]
        close_btn = target_page.locator("button[class*='close'], .universe-icon[data-icon='CloseOutlined'], [class*='header-close'], [class*='close']").first
        if await close_btn.count() > 0:
            print("Clicking close button...")
            await close_btn.click(force=True)
            await asyncio.sleep(2)
        else:
            print("Close button not found. Trying Escape key...")
            await target_page.keyboard.press("Escape")
            await asyncio.sleep(2)
            
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/clean_grid.png")
        print("Saved clean grid screenshot to clean_grid.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
