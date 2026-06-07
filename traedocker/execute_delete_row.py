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
        
        # Click Delete Record option in the open context menu
        print("Locating Delete Record option...")
        delete_option = target_page.locator(".ud__menu-item, [class*='menu-item'], [class*='item']").filter(has_text="Delete Record").first
        if await delete_option.count() > 0:
            print("Clicking Delete Record...")
            await delete_option.click(force=True)
            await asyncio.sleep(2)
            
            # Check for confirmation modal and click Delete/Confirm
            confirm_btn = target_page.locator(".ud__modal button:has-text('Delete'), .ud__modal button:has-text('确定'), .ud__modal button:has-text('删除')").first
            if await confirm_btn.count() > 0 and await confirm_btn.is_visible():
                print("Confirmation modal detected. Clicking Delete...")
                await confirm_btn.click(force=True)
                await asyncio.sleep(3)
            else:
                # Try a broader locator for the confirm button
                confirm_btn_broad = target_page.locator("button:has-text('Delete'), button:has-text('删除')").first
                if await confirm_btn_broad.count() > 0:
                    print("Clicking Delete via broad locator...")
                    await confirm_btn_broad.click(force=True)
                    await asyncio.sleep(3)
        else:
            print("Delete Record option not found in context menu!")
            
        # Take screenshot to verify deletion
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/after_delete.png")
        print("Saved screenshot to after_delete.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
