import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        page = context.pages[0]
        
        await page.bring_to_front()
        await asyncio.sleep(1)
        
        # Click Add Record
        add_btn = page.locator('[data-e2e="bitable-add-record-btn"]').first
        if await add_btn.count() > 0:
            print("Found Add Record button. Clicking...")
            await add_btn.click(force=True)
            await asyncio.sleep(4)
            await page.screenshot(path="after_add_record_btn.png")
            print("Screenshot saved to after_add_record_btn.png")
        else:
            print("Add Record button not found!")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
