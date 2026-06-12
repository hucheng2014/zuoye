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
        
        info = await target_page.evaluate("""
            () => {
                const dialog = document.querySelector('.link-field-panel-editor');
                if (!dialog) return "Dialog not found";
                
                const canvas = dialog.querySelector('canvas');
                if (!canvas) return "Canvas not found";
                
                const path = [];
                let parent = canvas;
                while (parent && parent !== dialog) {
                    path.push({
                        tagName: parent.tagName,
                        className: parent.className,
                        id: parent.id,
                        rect: parent.getBoundingClientRect()
                    });
                    parent = parent.parentElement;
                }
                return path;
            }
        """)
        
        print("Canvas path to dialog root:")
        import json
        for idx, item in enumerate(info):
            r = item['rect']
            rect_str = f"x={r.get('x',0):.1f}, y={r.get('y',0):.1f}, w={r.get('width',0):.1f}, h={r.get('height',0):.1f}"
            print(f"[{idx}] {item['tagName']}.{item['className']} (ID: {item['id']}) Rect: {rect_str}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
