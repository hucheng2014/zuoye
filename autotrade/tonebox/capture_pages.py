import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        # Get all pages
        print("Pages count:", len(context.pages))
        for idx, page in enumerate(context.pages):
            try:
                title = await page.title()
                url = page.url
                print(f"[{idx}] Title: {title}, URL: {url}")
                # Save screenshot of this page
                await page.screenshot(path=f"/Users/xaa/zuoye/traedocker/popup_check_{idx}.png")
                print(f"Saved screenshot of page {idx}")
            except Exception as e:
                print(f"Failed to capture page {idx}: {e}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
