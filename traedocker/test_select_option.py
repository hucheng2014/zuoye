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
        
        # Helper to find row
        async def get_row(field_name):
            row = target_page.locator(".base_record_card_field_editor_wrapper, .bitable-field-item").filter(
                has=target_page.locator(".bitable-field-name, [class*='field-name']", has_text=field_name)
            ).first
            return row

        # Helper to select dropdown
        async def select_dropdown(field_name, option_text):
            print(f"Selecting dropdown '{field_name}' -> '{option_text}'")
            row = await get_row(field_name)
            
            # Click dropdown trigger
            trigger = row.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button']").first
            await trigger.click(force=True)
            await asyncio.sleep(1.5)
            
            # Locate option container
            dropdown_container = target_page.locator(".b-select-dropdown-container, .b-select-list, [class*='dropdown-container']").first
            option = dropdown_container.locator(".b-select-option, [class*='option']").filter(has_text=option_text).first
            
            print(f"Clicking option {option_text}...")
            await option.click(force=True)
            await asyncio.sleep(1.5)

        # Select both
        await select_dropdown("repo_type", "公有仓库")
        await select_dropdown("language", "Python")
        
        # Take screenshot
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/step_1_dropdown.png")
        print("Screenshot saved to step_1_dropdown.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
