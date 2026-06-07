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
        
        # 2. Click once to select/focus the cell at (340, 491)
        print("Clicking cell at (340, 491)...")
        await target_page.mouse.click(340, 491)
        await asyncio.sleep(1.0)
        
        # 3. Press Space to open the drawer
        print("Pressing Space...")
        await target_page.keyboard.press("Space")
        await asyncio.sleep(4.0)
        
        # 4. Check if record details card is open
        drawer_visible = await target_page.evaluate("""
            () => {
                const card = document.querySelector('.base-record-card, [class*="record-card"]');
                if (!card) return null;
                const titleEl = card.querySelector('[class*="record-title"], [class*="RecordTitle"], h1, [class*="modal-title"]');
                return titleEl ? titleEl.innerText.trim() : 'CARD_OPEN_WITHOUT_TITLE';
            }
        """)
        print("Is record drawer open?", drawer_visible)
        
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/check_space_491.png")
        print("Saved check_space_491.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
