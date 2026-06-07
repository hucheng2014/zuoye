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
        
        # From the last screenshot, B00001886 is at approximately y=360 in the browser
        # Let's hover exactly over B00001886 row
        # The row appears to be at y=360 in absolute browser coordinates
        
        # Try hovering at x=310, y=360 (row header area for B00001886)
        print("Moving mouse to B00001886 row (y=360)...")
        await target_page.mouse.move(310, 360)
        await asyncio.sleep(2)
        
        # Take screenshot to see if "+" appeared
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/hover_360_detail.png")
        print("Saved hover_360_detail.png")
        
        # Try to find + button via DOM
        plus_btns = await target_page.evaluate("""
            () => {
                const results = [];
                document.querySelectorAll('span, svg, path, button').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    // Look for SVG elements that might be the "+" icon
                    if (rect.width > 0 && rect.height > 0 && rect.width < 30 && rect.height < 30 &&
                        rect.y > 340 && rect.y < 390 && rect.x > 190 && rect.x < 450) {
                        results.push({
                            tag: el.tagName,
                            text: (el.innerText || '').trim().substring(0, 20),
                            class: el.className.toString().substring(0, 60),
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
        
        print("Elements near B00001886 row (y=340-390, x=190-450):")
        for el in plus_btns:
            print(f"  {el['tag']} text='{el['text']}' class='{el['class']}' at ({el['x']:.1f}, {el['y']:.1f}) {el['width']:.0f}x{el['height']:.0f}")
        
        # Try clicking different x positions at y=360 to find the "+" button
        # The "+" button for adding a child row appears just before the expand icon
        # Let's try x=425 to 440 at y=360
        for x_try in [420, 425, 430, 435, 440]:
            print(f"\nTrying to click + at x={x_try}, y=360...")
            await target_page.mouse.move(x_try, 360)
            await asyncio.sleep(0.5)
            
            # Check if something appeared
            btns = await target_page.evaluate(f"""
                () => {{
                    const results = [];
                    document.querySelectorAll('*').forEach(el => {{
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0 && rect.width < 40 && rect.height < 40 &&
                            Math.abs(rect.x + rect.width/2 - {x_try}) < 30 && Math.abs(rect.y + rect.height/2 - 360) < 20) {{
                            results.push({{
                                tag: el.tagName,
                                text: (el.innerText || '').trim().substring(0, 20),
                                class: el.className.toString().substring(0, 50),
                                x: rect.x,
                                y: rect.y
                            }});
                        }}
                    }});
                    return results;
                }}
            """)
            
            if btns:
                print(f"  Found {len(btns)} elements:")
                for btn in btns:
                    print(f"    {btn['tag']} text='{btn['text']}' class='{btn['class']}' at ({btn['x']:.1f}, {btn['y']:.1f})")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
