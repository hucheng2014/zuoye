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
        
        # 1. Close any open drawer or dialog first
        warning_exit_btn = target_page.locator(".ud__modal button:has-text('Exit'), .ud__modal button:has-text('取消'), [class*='modal'] button:has-text('Exit')").first
        if await warning_exit_btn.count() > 0 and await warning_exit_btn.is_visible():
            await warning_exit_btn.click(force=True)
            await asyncio.sleep(2)
            
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        if drawer_visible:
            close_btn = target_page.locator("button:has-text('Exit'), button:has-text('取消'), [class*='exit'], [class*='header-close']").first
            if await close_btn.count() > 0:
                await close_btn.click(force=True)
                await asyncio.sleep(2)
                
        # 2. Click Search and search B00001886
        search_box = target_page.locator("input[placeholder*='Search'], input[placeholder*='搜索']").first
        await search_box.click(force=True)
        await asyncio.sleep(0.5)
        await target_page.keyboard.press("Control+A")
        await target_page.keyboard.press("Backspace")
        await target_page.keyboard.type("B00001886")
        await asyncio.sleep(3)
        
        # 3. Double click on the grid area where the highlighted row is
        # Since B00001886 is visible in the grid (at the bottom under B00001629),
        # let's click at coordinate x=230, y=425 (which is approximately the B00001886 cell) to select it,
        # then press Space or Enter to open the record card.
        # Let's try double clicking or pressing space.
        print("Clicking cell B00001886...")
        await target_page.mouse.dblclick(230, 425)
        await asyncio.sleep(4)
        
        # Take a screenshot of the details
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/record_details.png")
        print("Saved record_details.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
