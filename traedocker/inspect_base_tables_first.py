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
        
        sidebar_items = await target_page.evaluate("""
            () => {
                const results = [];
                const elements = document.querySelectorAll('.bitable-sidebar-item, [class*="sidebar"] [class*="item"], [class*="nav"] [class*="item"], [class*="sidebar-node"]');
                elements.forEach(el => {
                    const text = el.innerText ? el.innerText.trim() : '';
                    if (text) {
                        results.push({
                            className: el.className,
                            text: text
                        });
                    }
                });
                return results;
            }
        """)
        
        print("First 16 sidebar items:")
        for idx, item in enumerate(sidebar_items[:16]):
            print(f"[{idx}] Text: {item['text']}, Class: {item['className']}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
