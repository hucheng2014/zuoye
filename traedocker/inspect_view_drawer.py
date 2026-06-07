import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        target_page = None
        for page in context.pages:
            title = await page.title()
            if "需求二正式作业表_BBS" in title and not title.startswith("\u202d"):
                target_page = page
                break
        if not target_page:
            target_page = context.pages[0]
            
        await target_page.bring_to_front()
        await asyncio.sleep(1)
        
        # Get children and outerHTML of all rows in the drawer
        drawer_html = await target_page.evaluate("""
            () => {
                const results = [];
                // Look for elements that look like row containers in detail/view mode
                const items = document.querySelectorAll('.bitable-field-item, [class*="detail-item"], [class*="field-row"]');
                items.forEach((item, idx) => {
                    const text = item.innerText || '';
                    if (text.includes('language')) {
                        results.push({
                            idx,
                            text: text.substring(0, 100),
                            html: item.outerHTML.substring(0, 1500)
                        });
                    }
                });
                return results;
            }
        """)
        
        print(f"Found {len(drawer_html)} language rows:")
        for idx, row in enumerate(drawer_html):
            print(f"Row [{idx}] Text: {row['text']}")
            print(row['html'])
            print("="*40)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
