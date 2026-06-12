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
        
        # Click Add Record
        print("Clicking Add Record...")
        add_btn = target_page.locator('[data-e2e="bitable-add-record-btn"], .bitable-append-records-btn-wrapper button').first
        await add_btn.click(force=True)
        
        # Wait for drawer
        submit_btn = target_page.locator("button:has-text('Submit'), button:has-text('确定'), [class*='submit']").first
        await submit_btn.wait_for(state="visible", timeout=10000)
        await asyncio.sleep(1)
        
        # Robust get_row
        async def get_row(field_name):
            wrapper_selectors = [
                ".base_record_card_field_editor_wrapper",
                ".bitable-node-container-wrapper-field"
            ]
            count = await target_page.locator(", ".join(wrapper_selectors)).count()
            for i in range(count):
                row = target_page.locator(", ".join(wrapper_selectors)).nth(i)
                label_loc = row.locator(".bitable-field-name, [class*='field-name'], [class*='field-label'], .bitable-field-item").first
                if await label_loc.count() > 0:
                    text = await label_loc.inner_text()
                    text_clean = text.replace('\u200b', '').strip().split('\n')[0]
                    if text_clean == field_name:
                        return row
            return None
            
        row = await get_row("父记录")
        if row:
            print("Clicking trigger...")
            await row.locator(".b-field-empty-value, [class*='editor'], [class*='cell'], [role='button']").first.click(force=True)
            await asyncio.sleep(3)
            
            # Print relation dialog DOM details
            info = await target_page.evaluate("""
                () => {
                    const dialogs = document.querySelectorAll('.ud__modal, .bitable-relation-dialog, [class*="modal"], [class*="dialog"]');
                    return Array.from(dialogs).map((d, idx) => {
                        // find inputs
                        const inputs = Array.from(d.querySelectorAll('input')).map(inp => ({
                            type: inp.type,
                            placeholder: inp.placeholder,
                            className: inp.className,
                            outerHTML: inp.outerHTML.substring(0, 200)
                        }));
                        return {
                            idx,
                            className: d.className,
                            inputs: inputs,
                            html: d.outerHTML.substring(0, 1000)
                        };
                    });
                }
            """)
            print(f"Found {len(info)} dialogs:")
            for d in info:
                print(f"[{d['idx']}] Class: {d['className']}")
                print(f"    Inputs: {d['inputs']}")
                print(f"    HTML Snippet: {d['html']}")
                print("="*40)
        else:
            print("父记录 row not found!")
            
        # Close new record drawer
        close_btn = target_page.locator("button:has-text('Exit'), button:has-text('取消'), [class*='exit']").first
        if await close_btn.count() > 0:
            await close_btn.click(force=True)
            await asyncio.sleep(2)
            
        # Dismiss warning popup
        back_btn = target_page.locator("button:has-text('Exit'), [class*='btn']:has-text('Exit')").first
        if await back_btn.count() > 0:
            await back_btn.click(force=True)
            await asyncio.sleep(2)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
