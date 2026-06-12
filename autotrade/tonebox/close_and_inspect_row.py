import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
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
            
        print(f"Lark page: {await target_page.title()}")
        
        # Close the detail drawer first using ESC
        print("Closing drawer with Escape...")
        await target_page.keyboard.press("Escape")
        await asyncio.sleep(1)
        
        # Check for unsaved changes dialog
        exit_btn = target_page.locator("button:has-text('Exit'), button:has-text('不保存'), button:has-text('Discard')").first
        if await exit_btn.count() > 0 and await exit_btn.is_visible():
            await exit_btn.click(force=True)
            await asyncio.sleep(1)
        
        # Take screenshot to see current state
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/after_close_drawer.png")
        print("Saved after_close_drawer.png")
        
        # Hover over the B00001886 row to reveal the + button for adding child records
        # The row is at approximately y=360 in our screenshot
        # When we hover, a "+" should appear to add child record
        print("Hovering over B00001886 row to see child add button...")
        await target_page.mouse.move(350, 360)
        await asyncio.sleep(1.5)
        
        await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/hover_b1886_row.png")
        print("Saved hover_b1886_row.png")
        
        # Look for visible "+" buttons in the row area
        plus_btns = await target_page.evaluate("""
            () => {
                const results = [];
                document.querySelectorAll('button, [class*="add-child"], [class*="insert"]').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0 && rect.y > 300 && rect.y < 420) {
                        const text = el.innerText || el.textContent || '';
                        results.push({
                            text: text.trim().substring(0, 50),
                            x: rect.x + rect.width/2,
                            y: rect.y + rect.height/2,
                            class: el.className.substring(0, 80)
                        });
                    }
                });
                return results;
            }
        """)
        
        print("Buttons near B00001886 row (y=300-420):")
        for btn in plus_btns:
            print(f"  Text: '{btn['text']}', Coords: ({btn['x']}, {btn['y']}), Class: {btn['class']}")
        
        # In Lark Base, to add a child record, there is typically a "+" icon at the right of the row
        # When the row is selected or hovered.
        # Let me try to look at the row expand/child button
        # Looking at the screenshot, B00001886 row shows "⊞ 1" - possibly meaning 1 child
        # Let me check what happens if we click the expand icon
        
        # First check if there are already any child rows
        # The "⊞ 1" in the row header of B00001629 suggests it has 7 child records (shown as "↳7")
        # Let's look for the "+ add child" button
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
