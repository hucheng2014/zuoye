import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        # Select target page
        target_page = None
        for idx, page in enumerate(context.pages):
            title = await page.title()
            if "需求二正式作业表_BBS" in title and not title.startswith("\u202d"):
                target_page = page
                print(f"Selected Page [{idx}]: {title}")
                break
                
        if not target_page:
            for idx, page in enumerate(context.pages):
                url = page.url
                if "bytedance.larkoffice.com" in url:
                    target_page = page
                    print(f"Fallback to Page [{idx}]: {await page.title()}")
                    break
                    
        if not target_page:
            print("No Lark page found!")
            await browser.close()
            return
            
        await target_page.bring_to_front()
        await asyncio.sleep(2)
        
        # Helper to find row wrapper exactly
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
            
        # Helper to fill text field
        async def fill_text(field_name, value):
            print(f"Filling '{field_name}' -> '{value}'")
            row = await get_row(field_name)
            if not row:
                print(f"Error: Row for {field_name} not found!")
                return
            input_el = row.locator("input, textarea, [class*='editor'], [contenteditable='true']").first
            await input_el.click(force=True)
            await asyncio.sleep(0.5)
            await target_page.keyboard.press("Control+A")
            await target_page.keyboard.press("Backspace")
            await target_page.keyboard.type(value)
            await asyncio.sleep(1)
            
        # Helper to select dropdown value
        async def select_dropdown(field_name, option_text):
            print(f"Selecting dropdown '{field_name}' -> '{option_text}'")
            row = await get_row(field_name)
            if not row:
                print(f"Error: Row for {field_name} not found!")
                return
            # Find the value box/button to click
            await row.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button'], .bitable-select-view").first.click(force=True)
            await asyncio.sleep(2)
            # Find option
            option = target_page.locator(".ud__select-option, [role='option'], .ud__dropdown-menu-item, div").filter(has_text=option_text).first
            await option.click(force=True)
            await asyncio.sleep(1)
            await target_page.keyboard.press("Escape")
            await asyncio.sleep(1)

        # 1. Handle relation selection dialog - it's already open, but let's confirm B00001573 is selected
        dialog = target_page.locator('.link-field-panel-editor').first
        canvas = dialog.locator('canvas').first
        box = await canvas.bounding_box()
        if not box:
            print("Error: Canvas bounding box not found!")
            await browser.close()
            return
            
        print(f"Canvas box: {box}")
        
        # Click on the row text (offset x=200, y=60 relative to canvas) to select B00001573
        click_x = box['x'] + 200
        click_y = box['y'] + 60
        print(f"Clicking row text on canvas: x={click_x}, y={click_y}")
        await target_page.mouse.click(click_x, click_y)
        await asyncio.sleep(1.5)
        
        # Click Confirm button
        print("Clicking Confirm button...")
        confirm_btn = dialog.locator("button:has-text('Confirm'), button:has-text('确定')").first
        await confirm_btn.click(force=True)
        await asyncio.sleep(2.5)

        # 2. Fill prompt details for Prompt 1
        prompt_text = "请详细解释一下 `src/timesheet/services/entry_service.py` 中 `_calc_duration` 方法的实现逻辑，它是如何计算工时并处理跨天情况的？另外，为什么旧的 `old_duration_calc` 方法被废弃了，它存在什么精度和边界计算问题？"
        
        await fill_text("prompt_index", "1")
        await fill_text("prompt", prompt_text)
        await select_dropdown("difficulty", "简单")
        await select_dropdown("category", "代码理解与分析")
        await fill_text("tech_stack", "Python")
        await fill_text("module_tags", "EntryService")
        
        print("Fields filled. Taking preview screenshot...")
        preview_path = "/home/jianglei/zuoye/traedocker/prompt_1_filled.png"
        await target_page.screenshot(path=preview_path)
        print(f"Saved preview to {preview_path}")
        
        # 3. Submit
        print("Clicking Submit...")
        submit_btn = target_page.locator("button:has-text('Submit'), button:has-text('确定'), [class*='submit']").first
        await submit_btn.click(force=True)
        await asyncio.sleep(5)
        
        final_path = "/home/jianglei/zuoye/traedocker/prompt_1_submitted.png"
        await target_page.screenshot(path=final_path)
        print(f"Saved final screenshot to {final_path}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
