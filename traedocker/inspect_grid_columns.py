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
        
        # 1. Click "人员&repo信息" in sidebar to return to grid view
        # In popup_check_0.png, it is at top of sidebar
        print("Clicking '人员&repo信息' in sidebar...")
        await target_page.mouse.click(60, 125)
        await asyncio.sleep(2)
        
        # 2. Click in the middle of the grid to focus (e.g. x=500, y=250)
        print("Clicking grid viewport...")
        await target_page.mouse.click(500, 250)
        await asyncio.sleep(1)
        
        # 3. Press Right arrow key multiple times to scroll grid horizontally
        print("Pressing ArrowRight...")
        for _ in range(30):
            await target_page.keyboard.press("ArrowRight")
            await asyncio.sleep(0.05)
            
        await asyncio.sleep(2)
        
        # Take screenshot of the grid columns
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/grid_columns_right.png")
        print("Saved grid_columns_right.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
