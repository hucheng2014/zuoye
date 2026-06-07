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
        
        # Find HTML elements containing text B00001886
        elements_info = await target_page.evaluate("""
            () => {
                const list = [];
                // Search all elements in the document
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
                let node;
                while (node = walker.nextNode()) {
                    if (node.innerText && node.innerText.includes('B00001886')) {
                        // Check if it's a leaf-ish element or row container
                        if (node.children.length < 5) {
                            const rect = node.getBoundingClientRect();
                            list.push({
                                tagName: node.tagName,
                                className: node.className,
                                text: node.innerText.trim(),
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height
                            });
                        }
                    }
                }
                return list.slice(0, 10); // return first 10
            }
        """)
        
        print("Elements containing 'B00001886':")
        for el in elements_info:
            print(f"Tag: {el['tagName']}, Class: '{el['className']}', Text: '{el['text']}' at ({el['x']}, {el['y']}, {el['width']}, {el['height']})")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
