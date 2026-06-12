import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        # Select the Page without the invisible prefix (usually Page 2 in the pages list)
        target_page = None
        for idx, page in enumerate(context.pages):
            title = await page.title()
            if "需求二正式作业表_BBS" in title and not title.startswith("\u202d"):
                target_page = page
                print(f"Selected Page [{idx}]: {title}")
                break
                
        if not target_page:
            # fallback to first Lark page
            for idx, page in enumerate(context.pages):
                url = page.url
                if "bytedance.larkoffice.com" in url:
                    target_page = page
                    print(f"Fallback to Page [{idx}]: {await page.title()}")
                    break
                    
        if not target_page:
            print("No Lark page found!")
            await browser.close()
            return
            
        await target_page.bring_to_front()
        await asyncio.sleep(2)
        
        # Click Back to Edit if showing
        text = await target_page.evaluate("() => document.body.innerText")
        if "Back to Edit" in text:
            print("Clicking 'Back to Edit'...")
            back_btn = target_page.locator("button:has-text('Back to Edit'), [class*='btn']:has-text('Back to Edit')").first
            await back_btn.click(force=True)
            await asyncio.sleep(2)
            
        # Check if drawer is open
        drawer_visible = await target_page.evaluate("""
            () => {
                const drawer = document.querySelector('.base-record-card, [class*="record-card"], [class*="drawer-content"]');
                return !!drawer;
            }
        """)
        
        if not drawer_visible:
            print("Drawer is closed. Clicking + Add Record to open it...")
            add_btn = target_page.locator('[data-e2e="bitable-add-record-btn"]').first
            await add_btn.click(force=True)
            await asyncio.sleep(4)
            
        # Get all field names and values in the drawer
        fields_info = await target_page.evaluate("""
            () => {
                const results = [];
                // Look for fields
                const items = document.querySelectorAll('.base_record_card_field_editor_wrapper, .bitable-field-item');
                items.forEach((item, idx) => {
                    const labelEl = item.querySelector('.bitable-field-name, [class*="field-name"], [class*="field-label"]');
                    const label = labelEl ? labelEl.innerText.trim() : 'NO_LABEL';
                    
                    // Try to get input value or selection value
                    const inputEl = item.querySelector('input, textarea');
                    let val = '';
                    if (inputEl) {
                        val = inputEl.value;
                    } else {
                        // try to get text of dropdown or attachment
                        const textEl = item.querySelector('[class*="value"], [class*="text"], [class*="cell"]');
                        if (textEl) {
                            val = textEl.innerText.trim();
                        }
                    }
                    results.push({ idx, label, val: val.substring(0, 100) });
                });
                return results;
            }
        """)
        
        print(f"Drawer fields found: {len(fields_info)}")
        for field in fields_info:
            print(f"Field [{field['idx']}] Label: '{field['label']}', Value: '{field['val']}'")
            
        # Take screenshot of the opened drawer (with a short timeout)
        try:
            await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/drawer_opened_check.png", timeout=5000)
            print("Screenshot saved to drawer_opened_check.png")
        except Exception as e:
            print("Screenshot failed:", e)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
