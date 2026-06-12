import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        target_page = None
        for page in context.pages:
            url = page.url
            if "bytedance.larkoffice.com" in url:
                target_page = page
                break
                
        if not target_page:
            print("No Lark page found!")
            await browser.close()
            return
            
        print(f"Lark page: {await target_page.title()}")
        
        # 1. Switch back to "人员&repo信息" grid view just in case
        await target_page.mouse.click(60, 125)
        await asyncio.sleep(2)
        
        # 2. Close any open drawer or warning modal first
        warning_exit_btn = target_page.locator(".ud__modal button:has-text('Exit'), .ud__modal button:has-text('取消'), [class*='modal'] button:has-text('Exit')").first
        if await warning_exit_btn.count() > 0 and await warning_exit_btn.is_visible():
            print("Closing warning modal...")
            await warning_exit_btn.click(force=True)
            await asyncio.sleep(2)
            
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        if drawer_visible:
            print("Drawer open. Closing it...")
            close_btn = target_page.locator("button:has-text('Exit'), button:has-text('取消'), [class*='exit'], [class*='header-close']").first
            if await close_btn.count() > 0:
                await close_btn.click(force=True)
                await asyncio.sleep(2)
        
        # 3. Click the main Add Record button at the top left of the grid
        print("Clicking main Add Record button...")
        add_btn = target_page.locator('[data-e2e="bitable-add-record-btn"]').first
        await add_btn.click(force=True)
        await asyncio.sleep(4)
        
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
            print(f"Filling '{field_name}' -> '{value[:30]}...'")
            row = await get_row(field_name)
            if not row:
                print(f"Error: Row for {field_name} not found!")
                return
            await row.evaluate("el => el.scrollIntoView({ block: 'center' })")
            await asyncio.sleep(0.5)
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
            await row.evaluate("el => el.scrollIntoView({ block: 'center' })")
            await asyncio.sleep(0.5)
            
            trigger = row.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button'], .bitable-select-view, .b-select-value-placeholder").first
            await trigger.click(force=True)
            await asyncio.sleep(2)
            
            option = target_page.locator(".b-select-list .b-select-option, [class*='select-dropdown'] .b-select-option").filter(has_text=option_text).first
            await option.evaluate("el => el.scrollIntoView({ block: 'nearest' })")
            await asyncio.sleep(0.5)
            await option.click(force=True)
            await asyncio.sleep(1.5)

        # 4. Select Parent Record B00001573
        parent_id = "B00001573"
        print(f"Selecting parent {parent_id}...")
        row = await get_row("父记录")
        if row:
            await row.evaluate("el => el.scrollIntoView({ block: 'center' })")
            await asyncio.sleep(0.5)
            trigger = row.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button']").first
            await trigger.click(force=True)
            await asyncio.sleep(3)
            
            dialog = target_page.locator('.link-field-panel-editor').first
            search_input = dialog.locator("input[placeholder*='Search'], input[placeholder*='搜索']").first
            await search_input.click(force=True)
            await asyncio.sleep(0.5)
            await target_page.keyboard.press("Control+A")
            await target_page.keyboard.press("Backspace")
            await target_page.keyboard.type(parent_id)
            await asyncio.sleep(2.5)
            
            canvas = dialog.locator('canvas').first
            box = await canvas.bounding_box()
            if not box:
                print("Error: Canvas box not found!")
                await browser.close()
                return
                
            click_x = box['x'] + 200
            click_y = box['y'] + 60
            print(f"Clicking parent on canvas: x={click_x}, y={click_y}")
            await target_page.mouse.click(click_x, click_y)
            await asyncio.sleep(2)
            
            confirm_btn = dialog.locator("button:has-text('Confirm'), button:has-text('确定')").first
            await confirm_btn.click(force=True)
            await asyncio.sleep(2.5)
        else:
            print("Error: '父记录' row not found!")
            await browser.close()
            return

        # 5. Fill fields for Prompt 2
        prompt_text = (
            "目前 `src/timesheet/services/entry_service.py` 中计时器功能使用了一个模块级别的内存字典 `self._timers` 模拟，导致应用重启时计时器状态会全部丢失。\n"
            "请将其升级为数据库持久化存储：\n"
            "1. 在 `TimeEntry` 模型中新增字段 `start_time_iso` (String) 和 `is_active_timer` (Boolean)。\n"
            "2. 修改 `start_timer`，让它在启动计时器时，如果当前用户已经有运行的计时器，应抛出 `ValueError(\"已有正在运行的计时器\")`，否则将计时器持久化到数据库。\n"
            "3. 修改 `stop_timer` 逻辑，从数据库查找当前用户激活的计时器并计算时长，保存为正式工时记录，并将计时器标记为失效。\n"
            "4. 相应重构数据访问层、Service 层逻辑 and `tests/test_entries.py` 中对应的单元测试。"
        )
        await fill_text("prompt_index", "2")
        await fill_text("prompt", prompt_text)
        await select_dropdown("difficulty", "中等")
        await select_dropdown("category", "代码重构")
        await fill_text("tech_stack", "Python")
        await fill_text("module_tags", "EntryService")
        
        # Save preview screenshot
        preview_path = "/Users/xaa/zuoye/traedocker/prompt_2_correct_filled.png"
        await target_page.screenshot(path=preview_path)
        print(f"Saved preview of Prompt 2 to {preview_path}")
        
        # 6. Click Submit
        print("Clicking Submit...")
        submit_btn = target_page.locator("button:has-text('Submit'), button:has-text('确定'), [class*='submit']").first
        await submit_btn.click(force=True)
        await asyncio.sleep(5)
        
        # Save submitted screenshot
        submit_path = "/Users/xaa/zuoye/traedocker/prompt_2_correct_submitted.png"
        await target_page.screenshot(path=submit_path)
        print(f"Saved submission screenshot of Prompt 2 to {submit_path}")
        
        await browser.close()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
