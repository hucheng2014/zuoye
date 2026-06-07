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
        
        # Get children before click
        children_before = await target_page.evaluate("""
            () => Array.from(document.body.children).map(el => ({ tag: el.tagName, class: el.className, id: el.id }))
        """)
        
        # 2. Right click on row header (x=135, y=458)
        print("Right-clicking row header...")
        await target_page.mouse.click(135, 458, button="right")
        await asyncio.sleep(2)
        
        # Get children after click and compare
        compare_data = await target_page.evaluate("""
            (before) => {
                const beforeSet = new Set(before.map(el => el.tag + '.' + el.class + '#' + el.id));
                const after = Array.from(document.body.children);
                const added = [];
                after.forEach(el => {
                    const key = el.tagName + '.' + el.className + '#' + el.id;
                    if (!beforeSet.has(key)) {
                        added.push({
                            tag: el.tagName,
                            class: el.className,
                            id: el.id,
                            html: el.outerHTML.slice(0, 1000)
                        });
                    }
                });
                return added;
            }
        """, children_before)
        
        print("Added children after right click:")
        for idx, child in enumerate(compare_data):
            print(f"Child [{idx}]: Tag={child['tag']}, Class='{child['class']}', ID='{child['id']}'")
            print("HTML Snippet:")
            print(child['html'])
            print("-" * 50)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
