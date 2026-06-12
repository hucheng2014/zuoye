import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        # Select target page
        target_page = None
        for idx, page in enumerate(context.pages):
            title = await page.title()
            if "需求二正式作业表_BBS" in title and not title.startswith("\u202d"):
                target_page = page
                break
        if not target_page:
            target_page = context.pages[0]
            
        await target_page.bring_to_front()
        
        # Get children info
        children_info = await target_page.evaluate("""
            () => {
                const items = document.querySelectorAll('.base_record_card_field_editor_wrapper, .bitable-field-item');
                let targetRow = null;
                for (let item of items) {
                    const labelEl = item.querySelector('.bitable-field-name, [class*="field-name"]');
                    if (labelEl && labelEl.innerText.includes('dockerfile')) {
                        targetRow = item;
                        break;
                    }
                }
                if (!targetRow) return "ROW NOT FOUND";
                
                // Find all clickable elements inside targetRow
                const clickables = targetRow.querySelectorAll('button, div, span, a');
                return Array.from(clickables).map(el => ({
                    tagName: el.tagName,
                    className: el.className,
                    innerText: el.innerText ? el.innerText.trim() : '',
                    id: el.id
                }));
            }
        """)
        
        print("Clickable children inside dockerfile row:")
        for idx, item in enumerate(children_info):
            print(f"[{idx}] Tag: {item['tagName']}, Class: {item['className']}, Text: '{item['innerText']}', ID: '{item['id']}'")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
