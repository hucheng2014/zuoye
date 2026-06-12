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
        
        # Bring B00001886 row into focus by hovering
        # From screenshot: B00001886 is at y=360
        # The "+" button appeared for B00001633 when hovered, at y=285 (row 5)
        # B00001886 is at y=360
        
        # Hover over B00001886 row (row header area)
        print("Hovering over B00001886 row...")
        await target_page.mouse.move(280, 360)
        await asyncio.sleep(1)
        
        # Take screenshot to see what appears
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/hover_b1886_detail.png")
        print("Saved hover_b1886_detail.png")
        
        # Check for visible "+" buttons in the area
        plus_info = await target_page.evaluate("""
            () => {
                const results = [];
                // Look for all visible elements with "+" or "add" functionality
                document.querySelectorAll('*').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0 && rect.width < 50 && rect.height < 50 &&
                        rect.y > 340 && rect.y < 400 && rect.x > 200 && rect.x < 500) {
                        const text = (el.innerText || el.textContent || '').trim();
                        results.push({
                            tag: el.tagName,
                            text: text.substring(0, 30),
                            class: el.className.substring(0, 60),
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height
                        });
                    }
                });
                return results;
            }
        """)
        
        print("Elements near B00001886 row (y=340-400):")
        for el in plus_info:
            print(f"  {el['tag']} text='{el['text']}' class='{el['class']}' at ({el['x']:.0f}, {el['y']:.0f}) size=({el['width']:.0f}x{el['height']:.0f})")
        
        # Also get the text at that specific row to confirm it's B00001886
        # Let's look at what the row shows
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
