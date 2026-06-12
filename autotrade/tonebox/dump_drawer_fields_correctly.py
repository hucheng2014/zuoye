import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        page = context.pages[0]
        
        await page.bring_to_front()
        await asyncio.sleep(1)
        
        # Click Add Record if drawer not open
        drawer_visible = await page.evaluate("() => !!document.querySelector('.base-record-card, [class*=\"record-card\"]')")
        if not drawer_visible:
            print("Clicking Add Record to open drawer...")
            await page.locator('[data-e2e="bitable-add-record-btn"], .bitable-append-records-btn-wrapper button').first.click(force=True)
            await asyncio.sleep(4)
            
        # Get all field names
        fields = await page.evaluate("""
            () => {
                const els = document.querySelectorAll('.bitable-field-name, [class*="field-name"], [class*="field-label"]');
                return Array.from(els).map(el => {
                    let text = el.innerText || el.textContent;
                    return text.replace(/\u200b/g, '').trim().split('\\n')[0];
                });
            }
        """)
        
        # Deduplicate
        seen = set()
        unique_fields = []
        for f in fields:
            if f and f not in seen:
                seen.add(f)
                unique_fields.append(f)
                
        print(f"Unique field names count: {len(unique_fields)}")
        for i, f in enumerate(unique_fields):
            print(f"  [{i}] '{f}'")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())