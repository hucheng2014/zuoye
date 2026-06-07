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
        
        # 1. Click sidebar grid tab to reset
        await target_page.mouse.click(60, 125)
        await asyncio.sleep(2)
        
        # 2. Hover over B00001886 cell (x=230, y=440)
        print("Hovering over B00001886...")
        await target_page.mouse.move(230, 440)
        await asyncio.sleep(1.5)
        
        # 3. Take screenshot to see if the Open button appeared
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/hover_state.png")
        print("Saved hover_state.png")
        
        # 4. In Lark Base, when you select a cell, you can also open it by pressing Space or Enter.
        # Let's click at (230, 440) and press Space.
        print("Clicking cell B00001886...")
        await target_page.mouse.click(230, 440)
        await asyncio.sleep(0.5)
        print("Pressing Space key...")
        await target_page.keyboard.press("Space")
        await asyncio.sleep(3)
        
        # Check if record details card is open
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        print("Is record details card open?", drawer_visible)
        
        # Take a screenshot
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/record_card_space.png")
        print("Saved record_card_space.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
