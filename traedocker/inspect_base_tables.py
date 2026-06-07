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
        
        # Inspect sidebar elements for table list
        sidebar_items = await target_page.evaluate("""
            () => {
                const results = [];
                // Look for sidebar navigation items
                const elements = document.querySelectorAll('.bitable-sidebar-item, [class*="sidebar"] [class*="item"], [class*="nav"] [class*="item"], [class*="sidebar-node"]');
                elements.forEach(el => {
                    const text = el.innerText ? el.innerText.trim() : '';
                    if (text) {
                        results.push({
                            className: el.className,
                            text: text,
                            outerHTML: el.outerHTML.substring(0, 300)
                        });
                    }
                });
                return results;
            }
        """)
        
        print(f"Found {len(sidebar_items)} sidebar items:")
        for idx, item in enumerate(sidebar_items):
            print(f"[{idx}] Text: {item['text']}")
            print(f"    Class: {item['className']}")
            print(f"    HTML: {item['outerHTML']}")
            print("-" * 30)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
