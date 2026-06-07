import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        page = context.pages[0]
        
        await page.bring_to_front()
        await asyncio.sleep(1)
        
        # Click Add Record if drawer not open
        drawer_visible = await page.evaluate("() => !!document.querySelector('.base-record-card, [class*=\"record-card\"]')")
        if not drawer_visible:
            print("Clicking Add Record to open drawer...")
            await page.locator('[data-e2e="bitable-add-record-btn"], .bitable-append-records-btn-wrapper button').first.click(force=True)
            await asyncio.sleep(4)
            
        print("\n--- Analysing Drawer Structure ---")
        # Evaluate to find tree/hierarchy selectors
        tree_info = await page.evaluate("""
            () => {
                const info = {
                    buttons: [],
                    addBtns: [],
                    panels: []
                };
                
                document.querySelectorAll('button').forEach(btn => {
                    const text = btn.innerText || '';
                    if (text.includes('Add') || text.includes('Sub') || text.includes('+')) {
                        info.buttons.push({ text: text.trim(), class: btn.className });
                    }
                });
                
                document.querySelectorAll('[class*="add"], [class*="plus"]').forEach(el => {
                     const text = el.innerText || '';
                     if (text.length < 20) {
                         info.addBtns.push({ text: text.trim(), class: el.className });
                     }
                });
                
                return info;
            }
        """)
        
        print("Buttons with 'Add'/'Sub'/'+':")
        for b in tree_info['buttons']:
            print(f"  - '{b['text']}' (Class: {b['class']})")
            
        print("\nElements with 'add' or 'plus' in class:")
        for a in tree_info['addBtns'][:15]: # Print first 15 to avoid spam
            print(f"  - '{a['text']}' (Class: {a['class']})")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
