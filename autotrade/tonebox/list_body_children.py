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
        
        # List all body children
        children = await target_page.evaluate("""
            () => Array.from(document.body.children).map(el => ({ tag: el.tagName, class: el.className, id: el.id }))
        """)
        
        print("Body direct children:")
        for idx, child in enumerate(children):
            print(f"[{idx}] {child['tag']} class='{child['class']}' id='{child['id']}'")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
