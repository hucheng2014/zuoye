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
        
        # Get the row with B00001573 inside the dialog
        row_html = await target_page.evaluate("""
            () => {
                const dialog = document.querySelector('.ud__modal, .bitable-relation-dialog, [class*="modal"], [class*="dialog"]');
                if (!dialog) return "Dialog not found";
                
                // Let's find any element containing 'B00001573'
                const xpath = "//*[contains(text(), 'B00001573')]";
                const result = document.evaluate(xpath, dialog, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                const element = result.singleNodeValue;
                if (!element) return "B00001573 element not found";
                
                // Find its ancestor row (e.g. role=row or class containing row or tr)
                let parent = element;
                while (parent && parent !== dialog) {
                    if (parent.getAttribute('role') === 'row' || 
                        parent.tagName === 'TR' || 
                        parent.className.includes('row') || 
                        parent.className.includes('cell') || 
                        parent.className.includes('grid')) {
                        return {
                            foundTagName: parent.tagName,
                            foundClassName: parent.className,
                            outerHTML: parent.outerHTML.substring(0, 2000),
                            parentTagName: parent.parentElement ? parent.parentElement.tagName : 'NONE',
                            parentClassName: parent.parentElement ? parent.parentElement.className : 'NONE',
                        };
                    }
                    parent = parent.parentElement;
                }
                
                return {
                    tagName: element.tagName,
                    className: element.className,
                    outerHTML: element.outerHTML.substring(0, 1000)
                };
            }
        """)
        
        print("HTML for row:")
        import json
        print(json.dumps(row_html, indent=2, ensure_ascii=False))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
