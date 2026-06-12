import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        page = context.pages[0]
        
        await page.bring_to_front()
        await asyncio.sleep(1)
        
        # Press Escape multiple times to close drawers/modals
        for _ in range(3):
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
            
        await page.screenshot(path="current_base_view2.png", full_page=True)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())