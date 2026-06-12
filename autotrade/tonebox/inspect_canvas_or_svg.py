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
                if (!dialog) return "Relation dialog not found";
                
                const canvasElements = Array.from(dialog.querySelectorAll('canvas')).map(c => ({
                    className: c.className,
                    width: c.width,
                    height: c.height,
                    outerHTML: c.outerHTML
                }));
                
                const svgElements = Array.from(dialog.querySelectorAll('svg')).map(s => ({
                    className: s.className,
                    outerHTML: s.outerHTML.substring(0, 200)
                }));
                
                const shadowRoots = [];
                const all = dialog.getElementsByTagName('*');
                for (let i = 0; i < all.length; i++) {
                    if (all[i].shadowRoot) {
                        shadowRoots.push({
                            tagName: all[i].tagName,
                            className: all[i].className
                        });
                    }
                }
                
                return {
                    canvasCount: canvasElements.length,
                    canvasElements,
                    svgCount: svgElements.length,
                    shadowRootsCount: shadowRoots.length,
                    shadowRoots
                };
            }
        """)
        
        print("Dialog internals:")
        import json
        print(json.dumps(info, indent=2, ensure_ascii=False))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
