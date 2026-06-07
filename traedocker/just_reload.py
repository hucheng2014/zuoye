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
        await target_page.reload()
        await asyncio.sleep(8)
        
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/clean_grid_final.png")
        print("Saved final screenshot to clean_grid_final.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
