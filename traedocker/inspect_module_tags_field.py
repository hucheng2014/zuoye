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
            
        row = await get_row("module_tags")
        if row:
            await row.evaluate("el => el.scrollIntoView({ block: 'center' })")
            await asyncio.sleep(0.5)
            
            # Print HTML details of module_tags row
            html = await row.evaluate("el => el.outerHTML")
            print("module_tags HTML:")
            print(html)
            
            # Click it and type to see what overlay appears
            input_el = row.locator("input, textarea, [class*='editor'], [contenteditable='true']").first
            await input_el.click(force=True)
            await asyncio.sleep(0.5)
            await target_page.keyboard.type("EntryService")
            await asyncio.sleep(2)
            
            # Take screenshot of module_tags after typing
            await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/module_tags_typing.png")
            print("Saved screenshot to module_tags_typing.png")
            
            # Print any new dropdowns or popups
            popups = await target_page.evaluate("""
                () => {
                    const list = [];
                    const elements = document.querySelectorAll('.b-select-list, [class*="select-list"], .ud__select-menu, [class*="dropdown"]');
                    elements.forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            list.push({
                                className: el.className,
                                text: el.innerText.trim(),
                                html: el.outerHTML.substring(0, 500)
                            });
                        }
                    });
                    return list;
                }
            """)
            print("Visible dropdowns/popups during typing:")
            import json
            print(json.dumps(popups, indent=2, ensure_ascii=False))
            
            # Close/dismiss typing by clicking outside
            await target_page.mouse.click(50, 50)
            await asyncio.sleep(1)
        else:
            print("Row module_tags not found!")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
