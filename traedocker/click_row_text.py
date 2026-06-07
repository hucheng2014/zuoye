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
        
        dialog = target_page.locator('.link-field-panel-editor').first
        canvas = dialog.locator('canvas').first
        
        box = await canvas.bounding_box()
        if not box:
            print("Canvas box not found!")
            await browser.close()
            return
            
        # Click on the row text (offset x=200, y=60)
        click_x = box['x'] + 200
        click_y = box['y'] + 60
        print(f"Clicking row text at screen coords: x={click_x}, y={click_y}")
        
        await target_page.mouse.click(click_x, click_y)
        await asyncio.sleep(2)
        
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/after_row_text_click.png")
        print("Saved screenshot to after_row_text_click.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
