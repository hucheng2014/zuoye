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
        
        # 1. Close any open drawer first
        await target_page.keyboard.press("Escape")
        await asyncio.sleep(0.5)
        
        # 2. Click '人员&repo信息' in sidebar to switch back to table view
        print("Switching back to table view...")
        await target_page.mouse.click(100, 125)
        await asyncio.sleep(3.0)
        
        # 3. Click Chevron 1 of Row 1 (Level 0) at x=215, y=198
        print("Clicking Chevron 1 at (215, 198)...")
        await target_page.mouse.click(215, 198)
        await asyncio.sleep(2.0)
        
        # 4. Click Chevron 2 of Row 2 (Level 1) at x=235, y=226
        print("Clicking Chevron 2 at (235, 226)...")
        await target_page.mouse.click(235, 226)
        await asyncio.sleep(2.0)
        
        # 5. Click Chevron 9 of Row 9 (Level 2) at x=255, y=422
        print("Clicking Chevron 9 at (255, 422)...")
        await target_page.mouse.click(255, 422)
        await asyncio.sleep(2.0)
        
        # Take a screenshot to verify expansion
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/expanded_collapsed_success.png")
        print("Saved expanded_collapsed_success.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
