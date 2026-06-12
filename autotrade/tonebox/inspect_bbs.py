import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        page = await context.new_page()
        
        url = "https://bytedance.larkoffice.com/base/B4SgbbhcyaJfwWsWHvcc1AtgnYd?table=tblcXB0RGGaHGm1r&view=vewxWP7trZ"
        print(f"Navigating to {url}...")
        await page.goto(url)
        await asyncio.sleep(10) # Lark Base takes some time to load
        
        title = await page.title()
        print(f"Loaded page: {title}")
        
        # Capture screenshot to visualize the table
        await page.screenshot(path="/Users/xaa/zuoye/traedocker/bbs_loaded.png")
        print("Screenshot saved to /Users/xaa/zuoye/traedocker/bbs_loaded.png")
        
        # Let's inspect the page's HTML structure for headings and headers
        headers = await page.evaluate("""
            () => {
                const results = [];
                // Lark base headers usually have text
                const elements = document.querySelectorAll('[class*="header"], [class*="column-name"], [class*="cell"]');
                elements.forEach(el => {
                    if (el.innerText && el.innerText.trim().length > 0 && el.innerText.trim().length < 50) {
                        results.push({
                            tagName: el.tagName,
                            className: el.className,
                            text: el.innerText.trim()
                        });
                    }
                });
                return results.slice(0, 50); // limit to 50 items
            }
        """)
        
        print("Visible header/cell elements:")
        for h in headers:
            print(f"Tag: {h['tagName']}, Class: {h['className']}, Text: {h['text']}")
            
        await page.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
