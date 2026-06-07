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
        
        # Close any open drawer first
        await target_page.keyboard.press("Escape")
        await asyncio.sleep(0.5)
        
        # 1. Reload the page for a clean state
        print("Reloading page...")
        await target_page.reload()
        await asyncio.sleep(6)
        
        # 2. Wait for formula calculation
        print("Waiting for formula calculation...")
        for i in range(30):
            text = await target_page.evaluate("() => document.body.innerText")
            if "Formula calculating" not in text and "正在计算" not in text:
                break
            await asyncio.sleep(1)
            
        await asyncio.sleep(2)
        
        # 3. Click Chevron of Row 1 (Level 0) at x=280, y=198
        print("Clicking Chevron 1 at (280, 198)...")
        await target_page.mouse.click(280, 198)
        await asyncio.sleep(2.0)
        
        # 4. Click Chevron of Row 2 (Level 1) at x=300, y=226
        print("Clicking Chevron 2 at (300, 226)...")
        await target_page.mouse.click(300, 226)
        await asyncio.sleep(2.0)
        
        # 5. Click Chevron of Row 9 (Level 2) at x=320, y=422
        print("Clicking Chevron 9 at (320, 422)...")
        await target_page.mouse.click(320, 422)
        await asyncio.sleep(2.0)
        
        # Take a screenshot to verify expansion
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/expanded_correct.png")
        print("Saved expanded_correct.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
