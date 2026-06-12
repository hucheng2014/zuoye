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
        
        # Ensure any open drawer is closed
        await target_page.keyboard.press("Escape")
        await asyncio.sleep(0.5)
        
        # Clear search box if visible to restore full table grid view
        search_clear = target_page.locator(".ud__input-search-clear, [class*='clear']").first
        if await search_clear.count() > 0 and await search_clear.is_visible():
            print("Clearing existing search...")
            await search_clear.click(force=True)
            await asyncio.sleep(1.5)
            
        canvas = target_page.locator(".bitable-table-view--content canvas, canvas").first
        box = await canvas.bounding_box()
        if not box:
            print("Canvas not found!")
            await browser.close()
            return
            
        print(f"Canvas box: {box}")
        
        # 1. Click Row 1 to focus it
        click_x = box['x'] + 200 # 440
        click_y = box['y'] + 50  # 198
        print(f"Clicking Row 1 at ({click_x}, {click_y})...")
        await target_page.mouse.click(click_x, click_y)
        await asyncio.sleep(1.0)
        
        # Open drawer to verify focus on Row 1
        await target_page.keyboard.press("Space")
        await asyncio.sleep(2.0)
        title = await target_page.evaluate("""
            () => {
                const card = document.querySelector('.base-record-card, [class*="record-card"]');
                if (!card) return null;
                const titleEl = card.querySelector('[class*="record-title"], [class*="RecordTitle"], h1, [class*="modal-title"]');
                return titleEl ? titleEl.innerText.trim() : 'NO_TITLE';
            }
        """)
        print(f"Row 1: {title}")
        await target_page.keyboard.press("Escape")
        await asyncio.sleep(1.0)
        
        if title != "B00001573":
            print("Failed to focus B00001573. Retrying click...")
            # Click more towards the center of the row text
            await target_page.mouse.click(box['x'] + 250, box['y'] + 50)
            await asyncio.sleep(1.0)
            await target_page.keyboard.press("Space")
            await asyncio.sleep(2.0)
            title = await target_page.evaluate("""
                () => {
                    const card = document.querySelector('.base-record-card, [class*="record-card"]');
                    if (!card) return null;
                    const titleEl = card.querySelector('[class*="record-title"], [class*="RecordTitle"], h1, [class*="modal-title"]');
                    return titleEl ? titleEl.innerText.trim() : 'NO_TITLE';
                }
            """)
            print(f"Row 1 (Retry): {title}")
            await target_page.keyboard.press("Escape")
            await asyncio.sleep(1.0)
            
        # Expand Row 1
        print("Expanding Row 1...")
        await target_page.keyboard.press("ArrowRight")
        await asyncio.sleep(2.0)
        
        # We will move down one-by-one and verify
        for step in range(12):
            print(f"\nStep {step+1}: Pressing ArrowDown...")
            await target_page.keyboard.press("ArrowDown")
            await asyncio.sleep(0.6)
            
            # Open drawer to verify what is active
            await target_page.keyboard.press("Space")
            await asyncio.sleep(2.0)
            title = await target_page.evaluate("""
                () => {
                    const card = document.querySelector('.base-record-card, [class*="record-card"]');
                    if (!card) return null;
                    const titleEl = card.querySelector('[class*="record-title"], [class*="RecordTitle"], h1, [class*="modal-title"]');
                    return titleEl ? titleEl.innerText.trim() : 'NO_TITLE';
                }
            """)
            print(f"  Active Row: {title}")
            await target_page.keyboard.press("Escape")
            await asyncio.sleep(1.0)
            
            if title == "B00001886":
                print("Found B00001886! Expanding it...")
                await target_page.keyboard.press("ArrowRight")
                await asyncio.sleep(2.0)
                
                # Move to child B00001938
                print("Moving to child B00001938...")
                await target_page.keyboard.press("ArrowDown")
                await asyncio.sleep(0.6)
                
                # Open B00001938
                await target_page.keyboard.press("Space")
                await asyncio.sleep(3.0)
                
                final_title = await target_page.evaluate("""
                    () => {
                        const card = document.querySelector('.base-record-card, [class*="record-card"]');
                        if (!card) return null;
                        const titleEl = card.querySelector('[class*="record-title"], [class*="RecordTitle"], h1, [class*="modal-title"]');
                        return titleEl ? titleEl.innerText.trim() : 'NO_TITLE';
                    }
                """)
                print(f"  Final Active Row: {final_title}")
                await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/b1938_navigated_step.png")
                break
            elif title == "B00001952":
                print("Hit B00001952! We missed B00001886. Let's trace back.")
                break
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
