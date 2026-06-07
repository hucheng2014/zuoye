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
        
        # From the last screenshot, B00001938 is at y≈386
        # Let's first click on that row and press Space to open
        
        # Escape any open record first
        await target_page.keyboard.press("Escape")
        await asyncio.sleep(1)
        
        # Click at B00001938 row (y=386)
        print("Clicking B00001938 row at y=386...")
        await target_page.mouse.click(340, 386)
        await asyncio.sleep(1)
        
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/b1938_selected.png")
        print("Saved b1938_selected.png")
        
        # Press Space to open the record
        print("Pressing Space to open record card...")
        await target_page.keyboard.press("Space")
        await asyncio.sleep(3)
        
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/b1938_card.png")
        print("Saved b1938_card.png")
        
        # Check if record card is open and get its title
        card_info = await target_page.evaluate("""
            () => {
                // Try to find the record card or modal
                const selectors = [
                    '.base-record-card',
                    '[class*="record-card"]',
                    '.bitable-record-card',
                    '[class*="RecordCard"]',
                    '[class*="record-modal"]'
                ];
                
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el) {
                        const rect = el.getBoundingClientRect();
                        return {
                            selector: sel,
                            text: (el.innerText || '').substring(0, 400),
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height
                        };
                    }
                }
                return null;
            }
        """)
        
        if card_info:
            print(f"Card found with selector: {card_info['selector']}")
            print(f"Card text preview: {card_info['text'][:200]}")
        else:
            print("No card found")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
