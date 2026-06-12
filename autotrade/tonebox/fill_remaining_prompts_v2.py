import asyncio
import os
from playwright.async_api import async_playwright

prompts_data = [
    {
        "index": "2",
        "prompt": (
            "目前 `src/timesheet/services/entry_service.py` 中计时器功能使用了一个模块级别的内存字典 `self._timers` 模拟，导致应用重启时计时器状态会全部丢失。\n"
            "请将其升级为数据库持久化存储：\n"
            "1. 在 `TimeEntry` 模型中新增字段 `start_time_iso` (String) 和 `is_active_timer` (Boolean)。\n"
            "2. 修改 `start_timer`，让它在启动计时器时，如果当前用户已经有运行的计时器，应抛出 `ValueError(\"已有正在运行的计时器\")`，否则将计时器持久化到数据库。\n"
            "3. 修改 `stop_timer` 逻辑，从数据库查找当前用户激活的计时器并计算时长，保存为正式工时记录，并将计时器标记为失效。\n"
            "4. 相应重构数据访问层、Service 层逻辑和 `tests/test_entries.py` 中对应的单元测试。"
        ),
        "difficulty": "中等",
        "category": "代码重构",
        "tech_stack": "Python",
        "module_tags": "EntryService"
    },
    {
        "index": "3",
        "prompt": (
            "目前在 `src/timesheet/services/entry_service.py` 中，用户创建工时时，系统只校验了单次工时是否超过上限（`settings.max_hours_per_day`）。\n"
            "我们需要将其升级为“今日累计总工时上限校验”：\n"
            "当用户通过 `create_entry` 创建记录时，系统应该先去数据库统计该用户在该日期已录入的全部工时之和（duration 累加），如果“已录入的累计工时”加上“当前准备创建的工时”超过了 `settings.max_hours_per_day`，则必须抛出 `ValueError(\"今日累计工时超过每日上限\")` 异常。请完成逻辑修改并在 `tests/test_entries.py` 中补充测试。"
        ),
        "difficulty": "中等",
        "category": "功能迭代",
        "tech_stack": "Python",
        "module_tags": "EntryService"
    },
    {
        "index": "4",
        "prompt": (
            "目前 `src/timesheet/utils/export.py` 中导出的 Excel 只有原始明细。我们需要在所有数据行写入完成后，添加一个美化后的汇总行：\n"
            "1. 在表格最下方留空一行，然后写入一行汇总行，首列单元格内容为“Total”。\n"
            "2. 在工时时长（`duration`）对应的列（假设为 D 列），写入 Excel 计算公式 `=SUM(D2:Dn)`，其中 n 为数据结束行号。\n"
            "3. 使用 `openpyxl` 的样式功能对“Total”这一行进行加粗处理，并设置单元格背景填充为淡灰色。\n"
            "4. 请在 `tests/test_reports.py` 中添加测试用例，验证生成的 Excel 是否包含正确的公式和样式定义。"
        ),
        "difficulty": "中等",
        "category": "功能迭代",
        "tech_stack": "Python",
        "module_tags": "ReportService"
    },
    {
        "index": "5",
        "prompt": (
            "我们需要为工时审批流引入权限控制。请进行如下重构：\n"
            "1. 在 `Project` 模型中新增字段 `manager_id` (Integer) 指代负责人。\n"
            "2. 更新 Pydantic 校验 Schema `src/timesheet/schemas/project_schema.py` 允许设置该字段。\n"
            "3. 修改 `src/timesheet/services/timesheet_service.py` 中的 `approve_timesheet` and `reject_timesheet` 方法：在操作时必须传入 `operator_id`，并校验操作人是否等于当前工时表关联项目的 `manager_id`，若无权操作则抛出 `PermissionError(\"无权审批该工时表\")`。请同步修改相关的测试。"
        ),
        "difficulty": "困难",
        "category": "功能迭代",
        "tech_stack": "Python",
        "module_tags": "TimesheetService"
    },
    {
        "index": "6",
        "prompt": (
            "我们需要对项目的生命周期状态做更细致的管控：\n"
            "1. 将 `Project` 模型中的布尔字段 `is_active` 改为枚举状态 `status`（包含值：`DRAFT`、`ONGOING`、`COMPLETED`、`SUSPENDED`）。\n"
            "2. 修改项目创建和任务创建规则：只允许状态为 `ONGOING` 的项目创建任务或记录工时。\n"
            "3. 如果项目处于 `COMPLETED` 或 `SUSPENDED` 状态，创建工时记录应抛出 `ValueError(\"当前项目不可录入工时\")` 异常。\n"
            "请重构所有受影响的 Schema、服务逻辑和数据访问层，并修正现有的测试。"
        ),
        "difficulty": "困难",
        "category": "代码重构",
        "tech_stack": "Python",
        "module_tags": "ProjectService"
    },
    {
        "index": "7",
        "prompt": (
            "我们需要在报表生成中支持弹性加班时长折算统计：\n"
            "1. 修改 `src/timesheet/schemas/report_schema.py` 中的报表返回 Schema，新增 `overtime_hours` 和 `weighted_billable_hours` 两个可选的统计输出字段。\n"
            "2. 修改 `src/timesheet/services/report_service.py` 中的 `generate_report` 逻辑：如果某用户在一天内记录的 `is_billable` 工时超过了 8 小时，则超过的部分计入 `overtime_hours`，且超过的部分在 `weighted_billable_hours` 中按 1.5 倍加权计算（例如某天工作了 10 小时，正常 8 小时 + 加班 2 * 1.5 = 11 小时）。\n"
            "请修改计算逻辑并为其添加测试用例。"
        ),
        "difficulty": "中等",
        "category": "功能迭代",
        "tech_stack": "Python",
        "module_tags": "ReportService"
    }
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
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
        
        print("Performing initial page reload to clear any warning modals...")
        await target_page.reload()
        await asyncio.sleep(8)
        
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
            
            # Find option inside the ACTIVE list ONLY (no comma fallbacks to hidden ones!)
            option = target_page.locator(".b-select-list .b-select-option").filter(has_text=option_text).first
            await option.evaluate("el => el.scrollIntoView({ block: 'nearest' })")
            await asyncio.sleep(0.5)
            await option.click(force=True)
            await asyncio.sleep(1.5)

        for data in prompts_data:
            print(f"\n=================== FILLING PROMPT {data['index']} ===================")
            
            # 1. Close any open drawer or warning modal first
            warning_exit_btn = target_page.locator(".ud__modal button:has-text('Exit'), .ud__modal button:has-text('取消'), [class*='modal'] button:has-text('Exit')").first
            if await warning_exit_btn.count() > 0 and await warning_exit_btn.is_visible():
                print("Warning modal visible. Closing it...")
                await warning_exit_btn.click(force=True)
                await asyncio.sleep(2)
                
            drawer_visible = await target_page.evaluate("""
                () => !!document.querySelector('.base-record-card, [class*="record-card"]');
            """)
            if drawer_visible:
                print("Drawer open. Closing it via Escape key...")
                await target_page.keyboard.press("Escape")
                await asyncio.sleep(2)
                if await warning_exit_btn.count() > 0 and await warning_exit_btn.is_visible():
                    await warning_exit_btn.click(force=True)
                    await asyncio.sleep(2)
            
            # Click outside to ensure grid is active
            await target_page.mouse.click(50, 50)
            await asyncio.sleep(1)
            
            # 2. Click Add Record
            print("Clicking Add Record...")
            add_btn = target_page.locator('[data-e2e="bitable-add-record-btn"], .bitable-append-records-btn-wrapper button').first
            await add_btn.click(force=True)
            await asyncio.sleep(4)
            
            # 3. Select Parent Record B00001573
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
                
            # 4. Fill fields
            await fill_text("prompt_index", data["index"])
            await fill_text("prompt", data["prompt"])
            await select_dropdown("difficulty", data["difficulty"])
            await select_dropdown("category", data["category"])
            await fill_text("tech_stack", data["tech_stack"])
            await fill_text("module_tags", data["module_tags"])
            
            # Save preview screenshot
            preview_path = f"/Users/xaa/zuoye/traedocker/prompt_{data['index']}_filled.png"
            await target_page.evaluate("() => { const d = document.querySelector('.base-record-card, [class*=\"record-card\"]'); if(d) d.scrollTop = 0; }")
            await asyncio.sleep(1)
            await target_page.screenshot(path=preview_path)
            print(f"Saved preview of Prompt {data['index']} to {preview_path}")
            
            # 5. Click Submit
            print("Clicking Submit...")
            submit_btn = target_page.locator("button:has-text('Submit'), button:has-text('确定'), [class*='submit']").first
            await submit_btn.click(force=True)
            await asyncio.sleep(5)
            
            # Save submitted screenshot
            submit_path = f"/Users/xaa/zuoye/traedocker/prompt_{data['index']}_submitted.png"
            await target_page.screenshot(path=submit_path)
            print(f"Saved submission screenshot of Prompt {data['index']} to {submit_path}")
            
        print("\nAll remaining prompts successfully filled and submitted!")
        
        # Close any open detail drawer at the end
        await target_page.keyboard.press("Escape")
        await asyncio.sleep(2)
            
        # Refresh page for clean visual state
        await target_page.reload()
        await asyncio.sleep(8)
        
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/all_prompts_submitted.png")
        print("Final clean screenshot saved to all_prompts_submitted.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
