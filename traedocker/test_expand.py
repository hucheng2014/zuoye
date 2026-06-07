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
        
        # 2. Reload the page for a clean state
        print("Reloading page...")
        await target_page.reload()
        await asyncio.sleep(6)
        
        # 3. Wait for formula calculation
        print("Waiting for formula calculation to finish...")
        for i in range(30):
            text = await target_page.evaluate("() => document.body.innerText")
            if "Formula calculating" not in text and "正在计算" not in text:
                break
            await asyncio.sleep(1)
            
        await asyncio.sleep(2)
        
        # 4. Click the chevron of Row 1 at (260, 198) to expand it
        print("Clicking chevron at (260, 198)...")
        await target_page.mouse.click(260, 198)
        await asyncio.sleep(3.0)
        
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/expanded_check.png")
        print("Saved expanded_check.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
