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
        
        # Helper to print inputs
        async def print_inputs(label):
            print(f"--- Inputs {label} ---")
            inputs = await target_page.evaluate("""
                () => {
                    const results = [];
                    document.querySelectorAll('input').forEach(el => {
                        results.push({
                            type: el.type,
                            id: el.id,
                            className: el.className,
                            outerHTML: el.outerHTML.substring(0, 300)
                        });
                    });
                    return results;
                }
            """)
            print(f"Found {len(inputs)} inputs:")
            for idx, inp in enumerate(inputs):
                if inp['type'] == 'file' or inp['id'] or 'upload' in inp['id'] or 'attach' in inp['id']:
                    print(f"[{idx}] Type: {inp['type']}, ID: {inp['id']}, Class: {inp['className']}")
                    print(f"    HTML: {inp['outerHTML']}")
        
        await print_inputs("Initial")
        
        # Get dockerfile row
        row = target_page.locator(".base_record_card_field_editor_wrapper, .bitable-field-item").filter(
            has=target_page.locator(".bitable-field-name, [class*='field-name']", has_text="dockerfile")
        ).first
        
        # Scroll and click
        await row.evaluate("el => el.scrollIntoView({ block: 'center' })")
        await asyncio.sleep(1)
        print("Clicking Add attachment...")
        await row.locator("button, .b-collapsed-attach-editor__btn, .bitable-card-edit-cell-editor-Attachment").first.click(force=True)
        await asyncio.sleep(2)
        
        await print_inputs("After click")
        
        # Close the dialog
        await target_page.keyboard.press("Escape")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
