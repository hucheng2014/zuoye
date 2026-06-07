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
        
        # 1. Reset sidebar view
        await target_page.mouse.click(60, 125)
        await asyncio.sleep(2)
        
        # 2. Right click on row header (x=135, y=458)
        print("Right-clicking row header...")
        await target_page.mouse.click(135, 458, button="right")
        await asyncio.sleep(2)
        
        # 3. Dump the outer HTML of the context menu
        menu_html = await target_page.evaluate("""
            () => {
                // Find potential menu container
                const menu = document.querySelector('.ud__menu, [class*="menu"], [class*="context-menu"], [role="menu"]');
                return menu ? menu.outerHTML : "Menu container not found!";
            }
        """)
        
        print("Menu HTML:")
        print(menu_html[:2000]) # print first 2000 chars
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
