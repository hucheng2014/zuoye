import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        page = await context.new_page()
        
        url = "https://bytedance.larkoffice.com/base/B4SgbbhcyaJfwWsWHvcc1AtgnYd?table=tblcXB0RGGaHGm1r&view=vewxWP7trZ"
        await page.goto(url)
        await asyncio.sleep(8)
        
        # Open drawer
        await page.locator(".bitable-append-records-btn-wrapper button").first.click()
        await asyncio.sleep(4)
        
        # Log HTML structure of the drawer fields
        drawer_html = await page.evaluate("""
            () => {
                // Find the parent element containing '题目 id'
                const firstLabel = Array.from(document.querySelectorAll('*')).find(el => el.innerText && el.innerText.trim() === '题目 id');
                if (firstLabel) {
                    // Let's traverse up a few levels to find the field container
                    let fieldRow = firstLabel;
                    for (let i = 0; i < 3; i++) {
                        if (fieldRow.parentElement) fieldRow = fieldRow.parentElement;
                    }
                    // Let's print the outerHTML of the parent of the first few fields
                    const parent = fieldRow.parentElement;
                    if (parent) {
                        return {
                            parentTagName: parent.tagName,
                            parentClassName: parent.className,
                            innerHTML: parent.innerHTML.substring(0, 5000) // first 5k characters of fields list
                        };
                    }
                }
                return { error: 'Label not found' };
            }
        """)
        
        if "error" in drawer_html:
            print("Error:", drawer_html["error"])
        else:
            print(f"Parent: {drawer_html['parentTagName']} class={drawer_html['parentClassName']}")
            print("HTML Snippet:")
            print(drawer_html["innerHTML"][:2500])
            
        await page.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
