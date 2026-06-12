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
        
        async def check_options(field_name):
            print(f"--- Options for {field_name} ---")
            # Click the dropdown to open it
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
            
            # Extract options from active dropdown overlays
            options = await page.evaluate("""
                () => {
                    // Lark Base dropdown overlay items usually have classes like select-option, option, list-item, select-menu-item
                    // Let's grab elements inside the active select popup.
                    // The popup is typically appended to the body and has a high z-index or absolute positioning
                    const popups = document.querySelectorAll('.ud__select-menu, .bitable-select-menu, [role="listbox"], .ud__select-option, .bitable-select-option');
                    return Array.from(popups).map(el => el.innerText.trim());
                }
            """)
            print("Dropdown texts:", options)
            
            # Click outside to close
            await page.mouse.click(50, 50)
            await asyncio.sleep(1)
            
        await check_options("repo_type")
        await check_options("language")
        
        await page.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
