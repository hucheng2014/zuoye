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
        
        # Check elements inside dialog
        rows_info = await target_page.evaluate("""
            () => {
                const dialog = document.querySelector('.ud__modal, .bitable-relation-dialog, [class*="modal"], [class*="dialog"]');
                if (!dialog) return "Dialog not found!";
                
                // Let's find all text containing B00001573
                const b_elements = [];
                const all = dialog.getElementsByTagName('*');
                for (let i = 0; i < all.length; i++) {
                    const el = all[i];
                    if (el.textContent && el.textContent.includes('B00001573')) {
                        b_elements.push({
                            tagName: el.tagName,
                            className: el.className,
                            text: el.textContent.substring(0, 100),
                            childrenCount: el.children.length
                        });
                    }
                }
                
                // Let's also look for grid rows specifically
                const grid_rows = [];
                const rows = dialog.querySelectorAll('[role="row"], tr, [class*="grid-row"], [class*="table-row"], [class*="row"]');
                rows.forEach((r, idx) => {
                    grid_rows.push({
                        idx,
                        tagName: r.tagName,
                        className: r.className,
                        text: r.innerText.substring(0, 100),
                        checkboxHtml: Array.from(r.querySelectorAll('input[type="checkbox"], [class*="checkbox"], [class*="selection"]')).map(c => c.outerHTML)
                    });
                });
                
                return {
                    b_elements: b_elements.slice(0, 10),
                    grid_rows: grid_rows.slice(0, 20)
                };
            }
        """)
        
        print("Rows info inside dialog:")
        print(rows_info)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
