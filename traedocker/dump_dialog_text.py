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
        
        text_info = await target_page.evaluate("""
            () => {
                const dialog = document.querySelector('.ud__modal, .bitable-relation-dialog, [class*="modal"], [class*="dialog"]');
                if (!dialog) return "Dialog element not found!";
                
                const innerText = dialog.innerText;
                const htmlLength = dialog.innerHTML.length;
                
                // Let's find any text matches
                const matches = [];
                const allElements = dialog.getElementsByTagName('*');
                for (let i = 0; i < allElements.length; i++) {
                    const el = allElements[i];
                    const txt = el.innerText || el.textContent;
                    if (txt && (txt.includes('B000') || txt.includes('B00001573') || txt.includes('1573'))) {
                        matches.push({
                            tagName: el.tagName,
                            className: el.className,
                            innerTextLength: txt.length,
                            innerText: txt.substring(0, 150),
                            hasChildren: el.children.length > 0
                        });
                    }
                }
                
                return {
                    innerText: innerText.substring(0, 2000),
                    htmlLength,
                    matchesCount: matches.length,
                    matches: matches.slice(0, 15)
                };
            }
        """)
        
        print("Dialog text info:")
        import json
        print(json.dumps(text_info, indent=2, ensure_ascii=False))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
