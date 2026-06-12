import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        # Find target page (Lark page)
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
            
        print(f"Inspecting Lark page: {await target_page.title()} ({target_page.url})")
        
        # Check if Back to Edit dialog is there
        text = await target_page.evaluate("() => document.body.innerText")
        if "Back to Edit" in text:
            print("Clicking 'Back to Edit'...")
            back_btn = target_page.locator("button:has-text('Back to Edit'), [class*='btn']:has-text('Back to Edit')").first
            await back_btn.click(force=True)
            await asyncio.sleep(2)
            
        # Get grid headers and cell contents
        grid_data = await target_page.evaluate("""
            () => {
                // Find all columns and headers
                const columns = Array.from(document.querySelectorAll('.bitable-grid-header-cell, [class*="header-cell"]')).map(el => el.innerText.trim());
                
                // Find all row records
                const rows = [];
                const rowElements = document.querySelectorAll('.bitable-grid-row, [class*="grid-row"]');
                rowElements.forEach(row => {
                    const cells = Array.from(row.querySelectorAll('.bitable-grid-cell, [class*="grid-cell"]')).map(cell => cell.innerText.trim());
                    rows.push(cells);
                });
                
                return { columns, rows };
            }
        """)
        
        print("Columns found in table grid:")
        print(grid_data['columns'])
        
        print(f"Rows found: {len(grid_data['rows'])}")
        for idx, row in enumerate(grid_data['rows']):
            print(f"Row [{idx}]: {row}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
