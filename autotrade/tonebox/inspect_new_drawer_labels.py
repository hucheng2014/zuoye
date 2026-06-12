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
        
        # Click Add Record
        print("Clicking Add Record...")
        add_btn = target_page.locator('[data-e2e="bitable-add-record-btn"], .bitable-append-records-btn-wrapper button').first
        await add_btn.click(force=True)
        await asyncio.sleep(4)
        
        # Dump labels
        labels = await target_page.evaluate("""
            () => {
                const results = [];
                const selectors = ['.bitable-node-container-wrapper-field', '.base_record_card_field_editor_wrapper', '.bitable-record-card-field-wrapper', '.bitable-field-item'];
                selectors.forEach(sel => {
                    const els = document.querySelectorAll(sel);
                    els.forEach((el, idx) => {
                        const lbl = el.querySelector('.bitable-field-name, [class*="field-name"], [class*="field-label"]');
                        if (lbl) {
                            results.push({
                                selector: sel,
                                idx,
                                text: lbl.innerText
                            });
                        }
                    });
                });
                return results;
            }
        """)
        
        print(f"Found {len(labels)} labels in new record drawer:")
        for idx, lbl in enumerate(labels):
            print(f"[{idx}] Sel: {lbl['selector']}, Text: {lbl['text'].strip().replace('\n', ' ')}")
            
        # Close drawer
        close_btn = target_page.locator("button:has-text('Exit'), button:has-text('取消'), [class*='exit']").first
        if await close_btn.count() > 0:
            await close_btn.click(force=True)
            await asyncio.sleep(2)
            
        # Dismiss warning popup
        back_btn = target_page.locator("button:has-text('Exit'), [class*='btn']:has-text('Exit')").first
        if await back_btn.count() > 0:
            await back_btn.click(force=True)
            await asyncio.sleep(2)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
