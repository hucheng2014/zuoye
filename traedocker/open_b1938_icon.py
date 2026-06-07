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
        
        # 2. Hover over the cell first to reveal the expand icon
        print("Hovering over cell at (340, 491)...")
        await target_page.mouse.move(340, 491)
        await asyncio.sleep(0.5)
        
        # 3. Click the expand icon on the right side of the cell
        print("Clicking expand icon at (445, 491)...")
        await target_page.mouse.click(445, 491)
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
        
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/check_icon_click.png")
        print("Saved check_icon_click.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
