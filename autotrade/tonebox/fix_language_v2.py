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
        
        # Helper to find row wrapper exactly
        async def get_row(field_name):
            wrapper_selectors = [
                ".bitable-node-container-wrapper-field",
                ".base_record_card_field_editor_wrapper",
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

        # Fix language field
        print("Locating language field row wrapper...")
        row = await get_row("language")
        if row:
            print("Clicking language dropdown trigger...")
            trigger = row.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button']").first
            await trigger.click(force=True)
            await asyncio.sleep(2)
            
            # Select Python
            print("Selecting Python...")
            option = target_page.locator(".b-select-dropdown-container").locator(".b-select-option").filter(has_text="Python").first
            await option.click()
            await asyncio.sleep(1.5)
            
            # Click row label to close
            print("Closing dropdown...")
            label = row.locator(".bitable-field-name, [class*='field-name']").first
            await label.click(force=True)
            await asyncio.sleep(2)
            
            print("Screenshot after fixing language...")
            await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/bbs_fixed_language.png")
            print("Saved to bbs_fixed_language.png")
        else:
            print("Language field row wrapper not found!")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
