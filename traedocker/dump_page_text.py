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
            
        # Get all elements containing B00001886 or B00001573
        elements = await target_page.evaluate("""
            () => {
                const results = [];
                const all = document.querySelectorAll('*');
                all.forEach(el => {
                    if (el.children.length === 0 && (el.innerText || el.textContent || '').includes('B0000')) {
                        const rect = el.getBoundingClientRect();
                        results.push({
                            tagName: el.tagName,
                            className: el.className,
                            text: (el.innerText || el.textContent).trim(),
                            rect: {
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height
                            }
                        });
                    }
                });
                return results;
            }
        """)
        
        print("Found elements with 'B0000':")
        for el in elements:
            print(f"Tag: {el['tagName']}, Class: {el['className']}, Text: '{el['text']}', Rect: {el['rect']}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
