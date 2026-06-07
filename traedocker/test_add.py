import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        page = await context.new_page()
        
        url = "https://bytedance.larkoffice.com/base/B4SgbbhcyaJfwWsWHvcc1AtgnYd?table=tblcXB0RGGaHGm1r&view=vewxWP7trZ"
        await page.goto(url)
        await asyncio.sleep(8)
        
        # Click the Add Record button
        print("Clicking Add Record button...")
        btn = page.locator(".bitable-append-records-btn-wrapper button").first
        await btn.click()
        await asyncio.sleep(4)
        
        # Take a screenshot to inspect the change
        await page.screenshot(path="/home/jianglei/zuoye/traedocker/after_add_btn.png")
        print("Screenshot saved to /home/jianglei/zuoye/traedocker/after_add_btn.png")
        
        # Check if there are input elements or if a new row has appeared
        row_count = await page.evaluate("""
            () => {
                // Return details about rows in the table
                const rows = document.querySelectorAll('[class*="row"], [class*="grid-row"]');
                return rows.length;
            }
        """)
        print("Number of row elements found:", row_count)
        
        await page.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
