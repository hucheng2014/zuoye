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
        
        # From the screenshot, B00001886 is at y≈360
        # When hovering over a row, a "+" button appears at around x=425
        # Let's hover over B00001886 and look for the + button
        
        # First, scroll to make sure grid is visible and B00001886 is in view
        canvas = target_page.locator(".bitable-table-view--content canvas, canvas").first
        box = await canvas.bounding_box()
        print(f"Canvas: {box}")
        
        # Based on the screenshot, the rows are at these y coordinates:
        # Header: ~148-180
        # B00001573: ~158 (row y=10 relative to canvas)
        # B00001629: ~183 (y=35 relative to canvas)
        # B00001630: ~208 (y=60)
        # B00001631: ~233 (y=85)
        # B00001632: ~259 (y=111)
        # B00001633: ~285 (y=137)
        # B00001634: ~310 (y=162)
        # B00001635: ~335 (y=187)
        # B00001886: ~360 (y=212)
        
        # The "+" button appeared at ~x=425 for B00001633 when hovered
        # Let's hover over B00001886 row first (at y=360)
        print("Moving to B00001886 row at y=360...")
        await target_page.mouse.move(350, 360)
        await asyncio.sleep(1.5)
        
        # Take screenshot to capture what appears
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/row_hover_b1886.png")
        print("Saved row_hover_b1886.png")
        
        # Now try to find and click the "+" button that should appear
        # Based on observation, it appears around x=425 for the hovered row
        print("Looking for + button near x=425, y=360...")
        await target_page.mouse.move(425, 360)
        await asyncio.sleep(0.5)
        
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/after_hover_plus.png")
        print("Saved after_hover_plus.png")
        
        # Click the + button
        print("Clicking + button at x=425, y=360...")
        await target_page.mouse.click(425, 360)
        await asyncio.sleep(3)
        
        # Check if a new record drawer/form opened
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        print(f"Is record card open? {drawer_visible}")
        
        # Check body text to see if any add dialog appeared
        body_text = await target_page.evaluate("() => document.body.innerText.substring(0, 500)")
        print(f"Body text: {body_text[:200]}")
        
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/after_plus_click.png")
        print("Saved after_plus_click.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
