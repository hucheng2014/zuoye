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
        
        # Helper to find field editor wrapper
        async def click_select_and_get_options(field_name):
            print(f"Clicking select trigger for '{field_name}'...")
            await page.evaluate(f"""
                () => {{
                    const names = Array.from(document.querySelectorAll('.bitable-field-name'));
                    const targetName = names.find(n => n.innerText.trim() === '{field_name}');
                    if (targetName) {{
                        let p = targetName;
                        while (p && !p.className.includes('base_record_card_field_editor_wrapper')) {{
                            p = p.parentElement;
                        }}
                        if (p) {{
                            const trigger = p.querySelector('.b-field-label__editor');
                            if (trigger) trigger.click();
                        }}
                    }}
                }}
            """)
            await asyncio.sleep(2)
            
            # Extract options on screen
            options = await page.evaluate("""
                () => {
                    const list = [];
                    // Bitable select dropdown menu items usually have specific classes or roles
                    const items = document.querySelectorAll('[class*="option"], [class*="item"], [class*="select-menu"]');
                    items.forEach(el => {
                        if (el.innerText && el.innerText.trim().length > 0 && el.innerText.trim().length < 50) {
                            list.push(el.innerText.trim());
                        }
                    });
                    return list;
                }
            """)
            print(f"Options visible for '{field_name}':", list(set(options)))
            
            # Click outside to close dropdown
            await page.mouse.click(50, 50)
            await asyncio.sleep(1)
            
        await click_select_and_get_options("repo_type")
        await click_select_and_get_options("language")
        
        await page.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
