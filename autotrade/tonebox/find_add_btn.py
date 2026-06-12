import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        page = await context.new_page()
        
        url = "https://bytedance.larkoffice.com/base/B4SgbbhcyaJfwWsWHvcc1AtgnYd?table=tblcXB0RGGaHGm1r&view=vewxWP7trZ"
        await page.goto(url)
        await asyncio.sleep(8)
        
        # Find elements containing 'Record'
        elements = await page.evaluate("""
            () => {
                const results = [];
                const all = document.querySelectorAll('*');
                all.forEach(el => {
                    if (el.innerText && el.innerText.includes('Record')) {
                        results.push({
                            tagName: el.tagName,
                            className: el.className,
                            innerText: el.innerText.trim(),
                            outerHTML: el.outerHTML.substring(0, 200)
                        });
                    }
                });
                return results;
            }
        """)
        print("Record-related elements found:")
        for idx, el in enumerate(elements[:20]):
            print(f"[{idx}] Tag: {el['tagName']}, Class: {el['className']}, Text: {el['innerText']}, HTML: {el['outerHTML']}")
            
        await page.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
