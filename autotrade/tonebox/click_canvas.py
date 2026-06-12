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
        
        # Clear search if any
        search_clear = target_page.locator(".ud__input-search-clear, [class*='clear']").first
        if await search_clear.count() > 0 and await search_clear.is_visible():
            await search_clear.click(force=True)
            await asyncio.sleep(1)
            
        # 2. Click exactly at the midpoint of B00001886 row (x=280, y=452)
        print("Clicking B00001886 at x=280, y=452...")
        await target_page.mouse.click(280, 452)
        await asyncio.sleep(0.5)
        
        # Press Space
        print("Pressing Space...")
        await target_page.keyboard.press("Space")
        await asyncio.sleep(3)
        
        # Check if details drawer is open
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        print("Is record details card open after Space?", drawer_visible)
        
        if not drawer_visible:
            # Try double click
            print("Double clicking B00001886 at x=280, y=452...")
            await target_page.mouse.dblclick(280, 452)
            await asyncio.sleep(3)
            drawer_visible = await target_page.evaluate("""
                () => !!document.querySelector('.base-record-card, [class*="record-card"]');
            """)
            print("Is record details card open after double click?", drawer_visible)
            
        # Save screenshot
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/after_canvas_click.png")
        print("Saved after_canvas_click.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
