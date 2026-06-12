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
        
        # Click sidebar tab to reset
        await target_page.mouse.click(60, 125)
        await asyncio.sleep(2)
        
        # Print all canvas elements, their class names, and bounding boxes
        canvases = target_page.locator("canvas")
        count = await canvases.count()
        print("Total canvas count:", count)
        for i in range(count):
            canvas = canvases.nth(i)
            class_name = await canvas.evaluate("el => el.className")
            box = await canvas.bounding_box()
            print(f"Canvas [{i}] class: '{class_name}', box: {box}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
