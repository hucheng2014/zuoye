import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        # Find page 0
        target_page = context.pages[0]
        print(f"Target page: {await target_page.title()} ({target_page.url})")
        await target_page.bring_to_front()
        await asyncio.sleep(1)
        
        # Click Back to Edit if visible
        text = await target_page.evaluate("() => document.body.innerText")
        if "Back to Edit" in text:
            print("Clicking 'Back to Edit'...")
            back_btn = target_page.locator("button:has-text('Back to Edit'), [class*='btn']:has-text('Back to Edit')").first
            await back_btn.click(force=True)
            await asyncio.sleep(2)
            
        # Get all field names
        fields = await target_page.evaluate("""
            () => {
                const els = document.querySelectorAll('.bitable-field-name, [class*="field-name"], [class*="field-label"]');
                return Array.from(els).map((el, idx) => ({
                    index: idx,
                    className: el.className,
                    text: el.innerText.trim()
                }));
            }
        """)
        
        print("All visible field name elements:")
        for f in fields:
            print(f"[{f['index']}] Class: {f['className']}, Text: '{f['text']}'")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
