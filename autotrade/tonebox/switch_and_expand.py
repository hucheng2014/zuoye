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
        
        # 2. Click '人员&repo信息' in sidebar (collapsed coords: x=60, y=125)
        print("Clicking '人员&repo信息' at (60, 125)...")
        await target_page.mouse.click(60, 125)
        await asyncio.sleep(4.0)
        
        # Take a screenshot to verify we are in table view
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/table_view_check_v2.png")
        print("Saved table_view_check_v2.png")
        
        # 3. Focus and select the first row B00001573
        # In collapsed sidebar mode, Column 1 is from x=180 to x=280, Row 1 is at y=198
        print("Clicking B00001573 cell at (250, 198)...")
        await target_page.mouse.click(250, 198)
        await asyncio.sleep(1.0)
        
        # 4. Expand Row 1 (B00001573)
        print("Expanding B00001573...")
        await target_page.keyboard.press("ArrowRight")
        await asyncio.sleep(1.5)
        
        # 5. Move to B00001629
        print("Moving to B00001629...")
        await target_page.keyboard.press("ArrowDown")
        await asyncio.sleep(0.5)
        
        # 6. Expand B00001629
        print("Expanding B00001629...")
        await target_page.keyboard.press("ArrowRight")
        await asyncio.sleep(1.5)
        
        # 7. Move down 7 times to select B00001886
        print("Moving down 7 times to B00001886...")
        for i in range(7):
            await target_page.keyboard.press("ArrowDown")
            await asyncio.sleep(0.5)
            
        # 8. Expand B00001886
        print("Expanding B00001886...")
        await target_page.keyboard.press("ArrowRight")
        await asyncio.sleep(1.5)
        
        # 9. Move down 1 time to select B00001938
        print("Moving down 1 time to B00001938...")
        await target_page.keyboard.press("ArrowDown")
        await asyncio.sleep(0.5)
        
        # 10. Press Space to open the drawer
        print("Pressing Space to open drawer...")
        await target_page.keyboard.press("Space")
        await asyncio.sleep(4.0)
        
        # Check if record drawer is open
        drawer_visible = await target_page.evaluate("""
            () => {
                const card = document.querySelector('.base-record-card, [class*="record-card"]');
                if (!card) return null;
                const titleEl = card.querySelector('[class*="record-title"], [class*="RecordTitle"], h1, [class*="modal-title"]');
                return titleEl ? titleEl.innerText.trim() : 'CARD_OPEN_WITHOUT_TITLE';
            }
        """)
        print("Is record drawer open?", drawer_visible)
        
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/b1938_navigated_keyboard.png")
        print("Saved b1938_navigated_keyboard.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
