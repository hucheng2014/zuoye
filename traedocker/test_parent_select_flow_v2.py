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
        
        # Wait for drawer to open
        print("Waiting for drawer Submit button...")
        submit_btn = target_page.locator("button:has-text('Submit'), button:has-text('确定'), [class*='submit']").first
        await submit_btn.wait_for(state="visible", timeout=10000)
        await asyncio.sleep(1.5)
        
        # Helper to find row wrapper exactly
        async def get_row(field_name):
            wrapper_selectors = [
                ".base_record_card_field_editor_wrapper",
                ".bitable-node-container-wrapper-field"
            ]
            count = await target_page.locator(", ".join(wrapper_selectors)).count()
            for i in range(count):
                row = target_page.locator(", ".join(wrapper_selectors)).nth(i)
                label_loc = row.locator(".bitable-field-name, [class*='field-name'], [class*='field-label'], .bitable-field-item").first
                if await label_loc.count() > 0:
                    text = await label_loc.inner_text()
                    text_clean = text.replace('\u200b', '').strip().split('\n')[0]
                    if text_clean == field_name:
                        return row
            return None

        # Select parent record B00001573
        parent_id = "B00001573"
        print(f"Selecting parent record {parent_id}...")
        row = await get_row("父记录")
        if row:
            trigger = row.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button']").first
            await trigger.click(force=True)
            await asyncio.sleep(3)
            
            # Find dialog and search
            dialog = target_page.locator(".ud__modal, .bitable-relation-dialog, [class*='modal'], [class*='dialog']").first
            search_input = dialog.locator("input[placeholder*='Search'], input[placeholder*='搜索']").first
            await search_input.click(force=True)
            await target_page.keyboard.type(parent_id)
            await asyncio.sleep(2)
            
            # Click checkbox of row with parent_id
            row_to_select = dialog.locator("div[role='row'], tr, [class*='grid-row'], [class*='table-row']").filter(has_text=parent_id).first
            checkbox = row_to_select.locator("input[type='checkbox'], [class*='checkbox'], [class*='selection']").first
            await checkbox.click(force=True)
            await asyncio.sleep(1.5)
            
            # Click Confirm button
            confirm_btn = dialog.locator("button:has-text('Confirm'), button:has-text('确定')").first
            await confirm_btn.click(force=True)
            await asyncio.sleep(2.5)
            
            # Take screenshot after selection
            await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/after_parent_select.png")
            print("Saved screenshot to after_parent_select.png")
        else:
            print("Row '父记录' not found!")
            
        # Close new record drawer
        print("Closing drawer...")
        close_btn = target_page.locator("button:has-text('Exit'), button:has-text('取消'), [class*='exit']").first
        if await close_btn.count() > 0:
            await close_btn.click(force=True)
            await asyncio.sleep(2)
            
        # Dismiss warning popup if any
        back_btn = target_page.locator("button:has-text('Exit'), [class*='btn']:has-text('Exit')").first
        if await back_btn.count() > 0:
            await back_btn.click(force=True)
            await asyncio.sleep(2)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
