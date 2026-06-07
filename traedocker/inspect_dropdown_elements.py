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
        
        # Ensure drawer is open
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        if not drawer_visible:
            print("Opening drawer...")
            await target_page.locator('[data-e2e="bitable-add-record-btn"]').first.click(force=True)
            await asyncio.sleep(3)
            
        # Helper to find row
        async def get_row(field_name):
            wrapper_selectors = [
                ".base_record_card_field_editor_wrapper",
                ".bitable-node-container-wrapper-field",
                ".bitable-record-card-field-wrapper",
                ".bitable-field-item"
            ]
            count = await target_page.locator(", ".join(wrapper_selectors)).count()
            for i in range(count):
                row = target_page.locator(", ".join(wrapper_selectors)).nth(i)
                label_loc = row.locator(".bitable-field-name, [class*='field-name'], [class*='field-label']").first
                if await label_loc.count() > 0:
                    text = await label_loc.inner_text()
                    text_clean = text.replace('\u200b', '').strip().split('\n')[0]
                    if text_clean == field_name:
                        return row
            return None
            
        # Click difficulty dropdown
        print("Clicking difficulty trigger...")
        row = await get_row("difficulty")
        trigger = row.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button'], .bitable-select-view").first
        await trigger.click(force=True)
        await asyncio.sleep(2)
        
        # Inspect popup elements
        elements_info = await target_page.evaluate("""
            () => {
                const results = [];
                // Look for elements that might contain dropdown text or options
                const all = document.querySelectorAll('*');
                for (let i = 0; i < all.length; i++) {
                    const el = all[i];
                    const cls = el.className || '';
                    if (typeof cls === 'string' && (
                        cls.includes('select') || 
                        cls.includes('option') || 
                        cls.includes('dropdown') || 
                        cls.includes('menu') || 
                        cls.includes('listbox')
                    )) {
                        // filter visible and containing text
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0 && el.innerText && el.innerText.trim().length > 0 && el.innerText.trim().length < 50) {
                            results.push({
                                tagName: el.tagName,
                                className: cls,
                                text: el.innerText.trim(),
                                rect: { x: rect.x, y: rect.y, w: rect.width, h: rect.height }
                            });
                        }
                    }
                }
                return results;
            }
        """)
        
        print("Found elements matching dropdown filter:")
        import json
        print(json.dumps(elements_info, indent=2, ensure_ascii=False))
        
        # Save screenshot
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/difficulty_dropdown_opened.png")
        print("Screenshot saved to difficulty_dropdown_opened.png")
        
        # Click outside to close
        await target_page.mouse.click(50, 50)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
