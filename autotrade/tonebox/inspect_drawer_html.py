import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        # Find target page (Lark page)
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
            
        print(f"Inspecting Lark page: {await target_page.title()} ({target_page.url})")
        
        # Check if Back to Edit dialog is there
        text = await target_page.evaluate("() => document.body.innerText")
        if "Back to Edit" in text:
            print("Clicking 'Back to Edit'...")
            back_btn = target_page.locator("button:has-text('Back to Edit'), [class*='btn']:has-text('Back to Edit')").first
            await back_btn.click(force=True)
            await asyncio.sleep(3)
            
        # Get drawer outer HTML or elements
        drawer_info = await target_page.evaluate("""
            () => {
                const results = [];
                // Look for elements with class containing drawer, card, side, panel
                const selectors = ['[class*="drawer"]', '[class*="card"]', '[class*="panel"]', '[class*="modal"]', '.base-record-card', '.bitable-field-item'];
                for (let selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        results.push({
                            selector,
                            count: elements.length,
                            first_class: elements[0].className,
                            first_text: elements[0].innerText ? elements[0].innerText.substring(0, 200) : ''
                        });
                    }
                }
                
                // Let's also check if there is an iframe
                const iframes = document.querySelectorAll('iframe');
                if (iframes.length > 0) {
                    results.push({
                        selector: 'iframe',
                        count: iframes.length,
                        first_class: iframes[0].className,
                        first_text: ''
                    });
                }
                
                return results;
            }
        """)
        
        print("DOM selectors inspection:")
        for res in drawer_info:
            print(f"Selector: {res['selector']}")
            print(f"  Count: {res['count']}")
            print(f"  First class: {res['first_class']}")
            print(f"  First text: {res['first_text'].replace('\\n', ' ')}")
            
        # Try a quick screenshot with a low timeout
        try:
            print("Taking page screenshot with 5s timeout...")
            await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/drawer_quick.png", timeout=5000)
            print("Screenshot saved to drawer_quick.png")
        except Exception as e:
            print("Screenshot failed:", e)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
