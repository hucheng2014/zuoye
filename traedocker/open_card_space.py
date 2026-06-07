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
        
        # 1. Click sidebar grid tab just to reset
        await target_page.mouse.click(60, 125)
        await asyncio.sleep(2)
        
        # 2. Click search clear if visible
        search_clear = target_page.locator(".ud__input-search-clear, [class*='clear']").first
        if await search_clear.count() > 0 and await search_clear.is_visible():
            await search_clear.click(force=True)
            await asyncio.sleep(1)
            
        # 3. Double click on B00001886 row.
        # In grid_updated.png, B00001886 is the 9th row (including parent B00001573 and Prompt 1 B00001629)
        # B00001573 is row 1 (y=200)
        # B00001629 is row 2 (y=230)
        # B00001630 is row 3 (y=260)
        # B00001631 is row 4 (y=290)
        # B00001632 is row 5 (y=320)
        # B00001633 is row 6 (y=350)
        # B00001634 is row 7 (y=380)
        # B00001635 is row 8 (y=410)
        # B00001886 is row 9 (y=440)
        # Let's double click at x=230, y=440 to open the record card.
        print("Double clicking cell B00001886 at y=440...")
        await target_page.mouse.dblclick(230, 440)
        await asyncio.sleep(3)
        
        # Check if record details card is open
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        print("Is record details card open?", drawer_visible)
        
        # Take a screenshot
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/record_card_open.png")
        print("Saved record_card_open.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
