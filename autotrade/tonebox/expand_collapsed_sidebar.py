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
        
        # 2. Click Chevron 1 of Row 1 (Level 0) at x=160, y=198
        print("Clicking Chevron 1 at (160, 198)...")
        await target_page.mouse.click(160, 198)
        await asyncio.sleep(2.0)
        
        # 3. Click Chevron 2 of Row 2 (Level 1) at x=180, y=226
        print("Clicking Chevron 2 at (180, 226)...")
        await target_page.mouse.click(180, 226)
        await asyncio.sleep(2.0)
        
        # 4. Click Chevron 9 of Row 9 (Level 2) at x=200, y=422
        print("Clicking Chevron 9 at (200, 422)...")
        await target_page.mouse.click(200, 422)
        await asyncio.sleep(2.0)
        
        # Take a screenshot to verify expansion
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/expanded_collapsed.png")
        print("Saved expanded_collapsed.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
