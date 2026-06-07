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
        
        # Close 'Back to Edit' popup if visible
        text = await target_page.evaluate("() => document.body.innerText")
        if "Back to Edit" in text:
            print("Clicking 'Back to Edit' first...")
            back_btn = target_page.locator("button:has-text('Back to Edit'), [class*='btn']:has-text('Back to Edit')").first
            await back_btn.click(force=True)
            await asyncio.sleep(2)
            
        # Inspect drawer
        fields_info = await target_page.evaluate("""
            () => {
                const items = document.querySelectorAll('.base_record_card_field_editor_wrapper, .bitable-field-item');
                return Array.from(items).map(item => {
                    // Try to get field label/name
                    const labelEl = item.querySelector('.bitable-field-name, [class*="label"], [class*="title"]');
                    const label = labelEl ? labelEl.innerText.trim() : '';
                    
                    // Inner text of item
                    const text = item.innerText ? item.innerText.trim() : '';
                    return { label, text: text.substring(0, 100) };
                });
            }
        """)
        
        print("Fields found in drawer:")
        for idx, item in enumerate(fields_info):
            print(f"[{idx}] Label: '{item['label']}', Text preview: '{item['text']}'")
            
        await target_page.screenshot(path="/home/jianglei/zuoye/traedocker/drawer_inspected.png")
        print("Screenshot saved to drawer_inspected.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
