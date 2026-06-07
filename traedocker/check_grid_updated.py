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
        
        # Click sidebar grid tab just in case
        await target_page.mouse.click(60, 125)
        await asyncio.sleep(2)
        
        # Click grid viewport to focus
        await target_page.mouse.click(500, 250)
        await asyncio.sleep(1)
        
        # Take a screenshot to see if Prompt 2 is there
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/grid_updated.png")
        print("Saved grid_updated.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
