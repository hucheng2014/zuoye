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
                const container = document.querySelector('.link-field-panel-table-container');
                if (!container) return "Container not found";
                
                // Helper to serialize an element tree simply
                function serialize(el, depth = 0) {
                    if (depth > 6) return "...";
                    const children = Array.from(el.children).map(c => serialize(c, depth + 1));
                    return {
                        tagName: el.tagName,
                        className: el.className,
                        id: el.id,
                        role: el.getAttribute('role'),
                        rect: el.getBoundingClientRect(),
                        children
                    };
                }
                
                return serialize(container);
            }
        """)
        
        print("Grid structure:")
        import json
        # Custom printer to print rect nicely
        def clean_rects(obj):
            if isinstance(obj, dict):
                if 'rect' in obj:
                    r = obj['rect']
                    obj['rect'] = f"x={r.get('x',0):.1f}, y={r.get('y',0):.1f}, w={r.get('width',0):.1f}, h={r.get('height',0):.1f}"
                for k, v in obj.items():
                    clean_rects(v)
            elif isinstance(obj, list):
                for item in obj:
                    clean_rects(item)
        clean_rects(info)
        print(json.dumps(info, indent=2, ensure_ascii=False))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
