import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        for idx, page in enumerate(context.pages):
            url = page.url
            if "bytedance.larkoffice.com" not in url:
                continue
                
            title = await page.title()
            print(f"\n--- Page [{idx}]: {title} ---")
            
            # Find elements with text containing "Record", "record", "添加", "新增"
            elements_info = await page.evaluate("""
                () => {
                    const results = [];
                    const allElements = document.querySelectorAll('button, div, span, a');
                    for (let el of allElements) {
                        const txt = el.innerText ? el.innerText.trim() : '';
                        if (txt.includes('Record') || txt.includes('record') || txt.includes('新增') || txt.includes('添加')) {
                            if (txt.length < 50) {
                                results.push({
                                    tagName: el.tagName,
                                    className: el.className,
                                    text: txt,
                                    outerHTML: el.outerHTML.substring(0, 150)
                                });
                            }
                        }
                    }
                    return results.slice(0, 30);
                }
            """)
            
            print(f"Found {len(elements_info)} candidate elements:")
            for item in elements_info:
                print(f"Tag: {item['tagName']}, Class: {item['className']}, Text: '{item['text']}', HTML: {item['outerHTML']}")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
