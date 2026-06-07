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
        
        # Ensure drawer is open (it should be open with B00001626 detail page, let's check)
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
            
        # Click category dropdown
        print("Clicking category trigger...")
        row = await get_row("category")
        await row.evaluate("el => el.scrollIntoView({ block: 'center' })")
        await asyncio.sleep(0.5)
        
        trigger = row.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button'], .bitable-select-view, .b-select-value-placeholder").first
        await trigger.click(force=True)
        await asyncio.sleep(2)
        
        # Inspect option texts and classes in dropdown
        options_info = await target_page.evaluate("""
            () => {
                const list = [];
                const elements = document.querySelectorAll('.b-select-option, [class*="select-option"], .ud__select-option');
                elements.forEach((el, idx) => {
                    const rect = el.getBoundingClientRect();
                    list.push({
                        idx,
                        className: el.className,
                        text: el.innerText.trim(),
                        visible: rect.width > 0 && rect.height > 0
                    });
                });
                return list;
            }
        """)
        
        print("Found dropdown options:")
        import json
        print(json.dumps(options_info, indent=2, ensure_ascii=False))
        
        # Scroll the target option into view and click
        option_text = "代码理解与分析"
        option_loc = target_page.locator(".b-select-option, [class*='select-option'], .ud__select-option").filter(has_text=option_text).first
        if await option_loc.count() > 0:
            print(f"Scrolling option '{option_text}' into view...")
            await option_loc.evaluate("el => el.scrollIntoView({ block: 'nearest' })")
            await asyncio.sleep(0.5)
            print(f"Clicking option '{option_text}'...")
            await option_loc.click(force=True)
            await asyncio.sleep(2)
        else:
            print(f"Option '{option_text}' not found in locators!")
            
        # Take screenshot
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/category_selection_test.png")
        print("Screenshot saved to category_selection_test.png")
        
        # Click outside to close
        await target_page.mouse.click(50, 50)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
