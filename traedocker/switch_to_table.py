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
        
        # Click on '人员&repo信息' in the sidebar at (100, 125)
        print("Clicking '人员&repo信息' in sidebar...")
        await target_page.mouse.click(100, 125)
        await asyncio.sleep(4.0)
        
        # Take a screenshot to verify
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/table_view_check.png")
        print("Saved table_view_check.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
