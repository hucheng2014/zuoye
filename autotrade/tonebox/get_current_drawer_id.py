import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        page = context.pages[0]
        
        # Get drawer title
        title = await page.locator(".base-record-card-header-title, [class*='header-title']").inner_text()
        print(f"Drawer title: {title}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
