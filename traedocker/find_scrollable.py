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
        
        # Find all scrollable containers inside the drawer
        scrollable_info = await target_page.evaluate("""
            () => {
                const card = document.querySelector('.base-record-card, [class*="record-card"]');
                if (!card) return "No card found";
                
                const results = [];
                const all = card.querySelectorAll('*');
                all.forEach(el => {
                    if (el.scrollHeight > el.clientHeight) {
                        const style = window.getComputedStyle(el);
                        if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
                            results.push({
                                tagName: el.tagName,
                                className: el.className,
                                scrollHeight: el.scrollHeight,
                                clientHeight: el.clientHeight,
                                overflowY: style.overflowY
                            });
                        }
                    }
                });
                return results;
            }
        """)
        
        print("Scrollable containers inside the drawer:")
        print(scrollable_info)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
