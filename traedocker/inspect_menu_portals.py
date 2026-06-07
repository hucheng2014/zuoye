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
        
        # Reset sidebar view just in case
        await target_page.mouse.click(60, 125)
        await asyncio.sleep(2)
        
        # Right click at B00001886 row (x=135, y=458)
        print("Right clicking B00001886...")
        await target_page.mouse.click(135, 458, button="right")
        await asyncio.sleep(2)
        
        # Check where the menu is inside the popup containers
        overlay_htmls = await target_page.evaluate("""
            () => {
                const results = {};
                
                const popup = document.querySelector('#pp_popup');
                if (popup && popup.innerText) results['pp_popup'] = { text: popup.innerText.trim(), html: popup.outerHTML.slice(0, 1000) };
                
                const popupContainer = document.querySelector('#pp_popupContainer');
                if (popupContainer && popupContainer.innerText) results['pp_popupContainer'] = { text: popupContainer.innerText.trim(), html: popupContainer.outerHTML.slice(0, 1000) };
                
                const globalOverlay = document.querySelector('.global-overlay-container');
                if (globalOverlay && globalOverlay.innerText) results['global-overlay-container'] = { text: globalOverlay.innerText.trim(), html: globalOverlay.outerHTML.slice(0, 1000) };
                
                return results;
            }
        """)
        
        for name, data in overlay_htmls.items():
            print(f"--- Container: {name} ---")
            print(f"Text content: '{data['text']}'")
            print(f"HTML Snippet:")
            print(data['html'])
            print("=" * 60)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
