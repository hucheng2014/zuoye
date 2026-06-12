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
        
        # We will use the search box to find B00001629
        # Click search box
        search_box = target_page.locator("input[placeholder*='Search'], input[placeholder*='搜索']").first
        await search_box.click(force=True)
        await asyncio.sleep(0.5)
        await target_page.keyboard.type("B00001629")
        await asyncio.sleep(3)
        
        # Take a screenshot to see if it is highlighted
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/search_result.png")
        print("Saved search_result.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
