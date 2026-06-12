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
        
        # B00001938 is at y≈387 (the new sub-record under B00001886)
        # Let's open its record by double-clicking or pressing Space
        
        # First click the row to select it
        print("Clicking B00001938 row...")
        await target_page.mouse.click(310, 387)
        await asyncio.sleep(0.5)
        
        # Press Space to open the record detail
        print("Pressing Space to open record...")
        await target_page.keyboard.press("Space")
        await asyncio.sleep(3)
        
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/b1938_open.png")
        print("Saved b1938_open.png")
        
        # Check if record card opened
        record_visible = await target_page.evaluate("""
            () => {
                const card = document.querySelector('.base-record-card, [class*="record-card"], .bitable-record-card');
                return card ? {found: true, text: (card.innerText || '').substring(0, 300)} : {found: false};
            }
        """)
        print(f"Record card visible: {record_visible}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
