import asyncio
import os
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
            
        print(f"Target page: {await target_page.title()}")
        await target_page.bring_to_front()
        await asyncio.sleep(1)
        
        # Click Back to Edit if visible
        back_btn = target_page.locator("button:has-text('Back to Edit'), [class*='btn']:has-text('Back to Edit')")
        if await back_btn.count() > 0:
            print("Clicking 'Back to Edit'...")
            await back_btn.first.click(force=True)
            await asyncio.sleep(2)
            
        # Ensure drawer is open
        drawer_visible = await target_page.evaluate("""
            () => !!document.querySelector('.base-record-card, [class*="record-card"]');
        """)
        if not drawer_visible:
            print("Opening drawer...")
            await target_page.locator('[data-e2e="bitable-add-record-btn"]').first.click(force=True)
            await asyncio.sleep(3)
            
        # Save screenshot after opening drawer
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/step_0_drawer.png", timeout=5000)
        
        # Helper to find row
        async def get_row(field_name):
            return target_page.locator(".base_record_card_field_editor_wrapper").filter(
                has=target_page.locator(".bitable-field-name, [class*='field-name']", has_text=field_name)
            ).first
            
        # 1. Fill vendor
        print("Filling 供应商...")
        row_vendor = await get_row("供应商")
        inp_vendor = row_vendor.locator("input, textarea, [class*='editor'], [contenteditable='true']").first
        await inp_vendor.click(force=True)
        await target_page.keyboard.press("Control+A")
        await target_page.keyboard.press("Backspace")
        await target_page.keyboard.type("长沙朗慧")
        await asyncio.sleep(1)
        
        # 2. Select repo_type
        print("Selecting repo_type...")
        row_rt = await get_row("repo_type")
        await row_rt.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button']").first.click(force=True)
        await asyncio.sleep(2)
        option_rt = target_page.locator(".ud__select-option, [role='option'], .ud__dropdown-menu-item, div").filter(has_text="公有仓库").first
        await option_rt.click(force=True)
        await asyncio.sleep(1)
        await target_page.keyboard.press("Escape")
        await asyncio.sleep(1)
        
        # Take screenshot after dropdowns
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/step_1_dropdown.png", timeout=5000)
        
        # 3. Upload Dockerfile
        print("Uploading Dockerfile...")
        row_df = await get_row("dockerfile")
        await row_df.evaluate("el => el.scrollIntoView({ block: 'center' })")
        await asyncio.sleep(1)
        
        # Take screenshot of row scrolled
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/step_2_scroll.png", timeout=5000)
        
        # Click upload button
        await row_df.locator("button, .b-collapsed-attach-editor__btn, .bitable-card-edit-cell-editor-Attachment").first.click(force=True)
        await asyncio.sleep(2)
        
        # Take screenshot of upload active
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/step_3_clicked.png", timeout=5000)
        
        # Check input existence via evaluate
        exists = await target_page.evaluate("() => !!document.querySelector('input#attachment-upload')")
        print(f"input#attachment-upload exists: {exists}")
        
        # Attempt upload
        try:
            print("Setting input files...")
            await target_page.set_input_files("input#attachment-upload", "/home/jianglei/zuoye/traedocker/Dockerfile", timeout=5000)
            print("Successfully set input files!")
        except Exception as e:
            print("Failed to set input files:", e)
            
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/step_4_final.png", timeout=5000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
