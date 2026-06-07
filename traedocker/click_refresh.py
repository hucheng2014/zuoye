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
        
        # Look for Refresh button in modal
        refresh_btn = target_page.locator("button:has-text('Refresh'), button:has-text('刷新')").first
        if await refresh_btn.count() > 0 and await refresh_btn.is_visible():
            print("Clicking Refresh button in permissions changed modal...")
            await refresh_btn.click(force=True)
            await asyncio.sleep(8)
        else:
            print("Refresh button not found or not visible. Performing page reload...")
            await target_page.reload()
            await asyncio.sleep(8)
            
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/after_refresh.png")
        print("Saved screenshot to after_refresh.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
