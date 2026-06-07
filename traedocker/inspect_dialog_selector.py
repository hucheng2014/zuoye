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
        
        info = await target_page.evaluate("""
            () => {
                const results = [];
                // Query all elements that might be modals, dialogs or drawers
                const selectors = [
                    '.ud__modal', 
                    '.ud__modal__wrap',
                    '.ud__modal__body',
                    '.bitable-relation-dialog',
                    '[class*="modal"]',
                    '[class*="dialog"]',
                    '[class*="panel"]'
                ];
                
                selectors.forEach(sel => {
                    const elements = document.querySelectorAll(sel);
                    elements.forEach((el, idx) => {
                        results.push({
                            selector: sel,
                            idx,
                            tagName: el.tagName,
                            className: el.className,
                            innerText: (el.innerText || '').substring(0, 300),
                            hasB00001573: (el.innerText || '').includes('B00001573')
                        });
                    });
                });
                return results;
            }
        """)
        
        print("Found matching elements:")
        import json
        print(json.dumps(info, indent=2, ensure_ascii=False))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
