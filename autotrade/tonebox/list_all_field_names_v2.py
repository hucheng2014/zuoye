import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        print("Pages count:", len(context.pages))
        for idx, page in enumerate(context.pages):
            url = page.url
            if "bytedance.larkoffice.com" not in url:
                continue
                
            title = await page.title()
            print(f"\n--- Page [{idx}] Title: {title} ---")
            
            # Click Back to Edit if visible
            text = await page.evaluate("() => document.body.innerText")
            if "Back to Edit" in text:
                print("Clicking 'Back to Edit'...")
                back_btn = page.locator("button:has-text('Back to Edit'), [class*='btn']:has-text('Back to Edit')").first
                await back_btn.click(force=True)
                await asyncio.sleep(2)
                
            # Get all field names
            fields = await page.evaluate("""
                () => {
                    const els = document.querySelectorAll('.bitable-field-name, [class*="field-name"], [class*="field-label"]');
                    return Array.from(els).map((el, idx) => ({
                        index: idx,
                        className: el.className,
                        text: el.innerText.trim()
                    }));
                }
            """)
            
            print(f"Field names count: {len(fields)}")
            for f in fields[:30]:  # print up to 30 fields
                print(f"  [{f['index']}] Class: {f['className']}, Text: '{f['text']}'")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
