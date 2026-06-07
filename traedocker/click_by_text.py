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
        
        # 1. Reset sidebar view
        await target_page.mouse.click(60, 125)
        await asyncio.sleep(2)
        
        # 2. Right click on row header (x=135, y=458)
        print("Right-clicking row header...")
        await target_page.mouse.click(135, 458, button="right")
        await asyncio.sleep(2)
        
        # 3. Click using text locator
        print("Clicking Open Record using text locator...")
        try:
            # We look for "Open Record" or "展开记录"
            open_item = target_page.locator("text=Open Record, text=展开记录, [class*='menu'] >> text=Open Record").first
            await open_item.click(force=True)
            print("Clicked!")
        except Exception as e:
            print("Failed to click:", e)
            
        await asyncio.sleep(4)
        
        # Check if record details card is open
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        print("Is record details card open?", drawer_visible)
        
        # Take a screenshot
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/record_card_text_click.png")
        print("Saved record_card_text_click.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
