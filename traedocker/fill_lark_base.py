import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        # Close all Lark Base pages except one, to avoid tab confusion
        lark_pages = []
        for page in context.pages:
            url = page.url
            title = await page.title()
            if "bytedance.larkoffice.com" in url:
                lark_pages.append(page)
                
        print(f"Total Lark Base pages found: {len(lark_pages)}")
        
        # We keep only the first one, close the rest
        target_page = None
        if len(lark_pages) > 0:
            target_page = lark_pages[0]
            print(f"Keeping Lark page: {await target_page.title()} ({target_page.url})")
            for page in lark_pages[1:]:
                print(f"Closing extra Lark page: {await page.title()}")
                await page.close()
        else:
            # Create fresh
            print("No Lark pages found, creating new one...")
            target_page = await context.new_page()
            await target_page.goto("https://bytedance.larkoffice.com/base/B4SgbbhcyaJfwWsWHvcc1AtgnYd?table=tblcXB0RGGaHGm1r&view=vewxWP7trZ")
            await asyncio.sleep(8)
            print("Opening fresh drawer...")
            await target_page.locator(".bitable-append-records-btn-wrapper button").first.click(force=True)
            await asyncio.sleep(4)
            
        # Bring target page to front
        await target_page.bring_to_front()
        await asyncio.sleep(2)
        
        # Handle 'Back to Edit' dialog if it is showing
        text = await target_page.evaluate("() => document.body.innerText")
        if "Back to Edit" in text:
            print("Dialog is showing on target page. Clicking 'Back to Edit'...")
            back_btn = target_page.locator("button:has-text('Back to Edit'), [class*='btn']:has-text('Back to Edit')").first
            await back_btn.click(force=True)
            await asyncio.sleep(2)
            
        # Check if values are filled, if not fill them
        print("Checking initial values...")
        vendor_row = target_page.locator(".base_record_card_field_editor_wrapper").filter(has=target_page.locator(".bitable-field-name", has_text="供应商"))
        vendor_val = await vendor_row.locator("input, textarea, [class*='editor']").first.input_value()
        print("Current vendor value:", vendor_val)
        if not vendor_val:
            print("Filling 供应商 (Vendor)...")
            await vendor_row.locator("input, textarea, [class*='editor']").first.click(force=True)
            await target_page.keyboard.type("长沙朗慧")
            await asyncio.sleep(1)
            
        repo_url_row = target_page.locator(".base_record_card_field_editor_wrapper").filter(has=target_page.locator(".bitable-field-name", has_text="repo_url"))
        repo_url_val = await repo_url_row.locator("input, textarea, [class*='editor']").first.input_value()
        print("Current repo_url value:", repo_url_val)
        if not repo_url_val:
            print("Filling repo_url...")
            await repo_url_row.locator("input, textarea, [class*='editor']").first.click(force=True)
            await target_page.keyboard.type("无（业务方提供）")
            await asyncio.sleep(1)
            
        # Fill repo_type (公有仓库)
        print("Filling repo_type...")
        repo_type_row = target_page.locator(".base_record_card_field_editor_wrapper").filter(has=target_page.locator(".bitable-field-name", has_text="repo_type"))
        # Click the dropdown selector
        await repo_type_row.locator(".b-field-empty-value, [class*='editor'], [class*='cell']").first.click(force=True)
        await asyncio.sleep(2)
        await target_page.locator(".ud__select-option, [role='option'], div").filter(has_text="公有仓库").first.click(force=True)
        await asyncio.sleep(1)
        await target_page.keyboard.press("Escape")
        await asyncio.sleep(1)
        
        # Fill language (Python)
        print("Filling language...")
        lang_row = target_page.locator(".base_record_card_field_editor_wrapper").filter(has=target_page.locator(".bitable-field-name", has_text="language"))
        await lang_row.locator(".b-field-empty-value, [class*='editor'], [class*='cell']").first.click(force=True)
        await asyncio.sleep(2)
        await target_page.locator(".ud__select-option, [role='option'], div").filter(has_text="Python").first.click(force=True)
        await asyncio.sleep(1)
        await target_page.keyboard.press("Escape")
        await asyncio.sleep(1)
        
        # Upload Dockerfile
        print("Uploading Dockerfile...")
        dockerfile_row = target_page.locator(".base_record_card_field_editor_wrapper").filter(has=target_page.locator(".bitable-field-name", has_text="dockerfile"))
        async with target_page.expect_file_chooser() as fc_info:
            await dockerfile_row.locator("text=Add attachment, [class*='add-attachment'], [class*='upload']").first.click(force=True)
        file_chooser = await fc_info.value
        await file_chooser.set_files("/home/jianglei/zuoye/traedocker/Dockerfile")
        await asyncio.sleep(2)
        
        # Upload repo.zip
        print("Uploading repo.zip...")
        repo_row = target_page.locator(".base_record_card_field_editor_wrapper").filter(has=target_page.locator(".bitable-field-name", has_text="repo"))
        async with target_page.expect_file_chooser() as fc_info:
            await repo_row.locator("text=Add attachment, [class*='add-attachment'], [class*='upload']").first.click(force=True)
        file_chooser = await fc_info.value
        await file_chooser.set_files("/home/jianglei/zuoye/traedocker/repo.zip")
        await asyncio.sleep(2)
        
        # Fill environment_notes
        print("Filling environment_notes...")
        notes_row = target_page.locator(".base_record_card_field_editor_wrapper").filter(has=target_page.locator(".bitable-field-name", has_text="environment_notes"))
        await notes_row.locator("input, textarea, [class*='editor']").first.click(force=True)
        await target_page.keyboard.type("Python 3.11, FastAPI, openpyxl, SQLite")
        await asyncio.sleep(1)
        
        # Fill task_count
        print("Filling task_count...")
        task_count_row = target_page.locator(".base_record_card_field_editor_wrapper").filter(has=target_page.locator(".bitable-field-name", has_text="task_count"))
        await task_count_row.locator("input, textarea, [class*='editor']").first.click(force=True)
        await target_page.keyboard.type("7")
        await asyncio.sleep(1)
        
        # Upload dockerfile构建成功截图
        print("Uploading dockerfile构建成功截图...")
        screenshot_row = target_page.locator(".base_record_card_field_editor_wrapper").filter(has=target_page.locator(".bitable-field-name", has_text="dockerfile构建成功截图"))
        async with target_page.expect_file_chooser() as fc_info:
            await screenshot_row.locator("text=Add attachment, [class*='add-attachment'], [class*='upload']").first.click(force=True)
        file_chooser = await fc_info.value
        await file_chooser.set_files("/home/jianglei/zuoye/traedocker/docker_build_success.png")
        
        # Wait 8 seconds for all uploads to complete
        print("Waiting for file uploads to complete...")
        await asyncio.sleep(8)
        
        # Take preview screenshot
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/bbs_filled_preview.png")
        print("Preview screenshot saved.")
        
        # Click Submit button
        print("Clicking Submit button...")
        submit_btn = target_page.locator("button:has-text('Submit'), button:has-text('确定'), [class*='submit']").first
        await submit_btn.click(force=True)
        await asyncio.sleep(5)
        
        # Take final screenshot
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/bbs_after_submit.png")
        print("Final screenshot saved.")
        
        await target_page.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
