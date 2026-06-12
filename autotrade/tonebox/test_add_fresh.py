import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9235")
        context = browser.contexts[0]
        
        target_page = None
        for idx, page in enumerate(context.pages):
            title = await page.title()
            if "需求二正式作业表_BBS" in title and not title.startswith("\u202d"):
                target_page = page
                print(f"Selected Page [{idx}]: {title}")
                break
                
        if not target_page:
            target_page = context.pages[0]
            print(f"Fallback to Page [0]: {await target_page.title()}")
            
        await target_page.bring_to_front()
        await asyncio.sleep(2)
        
        # Click + Add Record button
        print("Looking for Add Record button...")
        add_btn_selectors = [
            '[data-e2e="bitable-add-record-btn"]',
            '.bitable-append-records-btn-wrapper button',
            'button:has-text("Add Record")',
            'button:has-text("添加记录")',
            '.bitable-add-record-btn'
        ]
        
        add_btn = None
        for sel in add_btn_selectors:
            loc = target_page.locator(sel).first
            if await loc.count() > 0:
                add_btn = loc
                print(f"Found Add Record button with selector: {sel}")
                break
                
        if add_btn:
            print("Clicking Add Record button...")
            await add_btn.click(force=True)
            await asyncio.sleep(4)
            await target_page.screenshot(path="/Users/xaa/zuoye/traedocker/after_add_btn.png")
            print("Screenshot saved to after_add_btn.png")
        else:
            print("No Add Record button found by selector list. Trying to find any button with 'Record' or '+'...")
            # Let's inspect buttons
            buttons = await target_page.evaluate("""
                () => {
                    const btnList = [];
                    document.querySelectorAll('button, div[role="button"]').forEach(el => {
                        btnList.push({
                            text: el.innerText ? el.innerText.trim() : '',
                            className: el.className,
                            html: el.outerHTML.substring(0, 150)
                        });
                    });
                    return btnList;
                }
            """)
            print(f"Found {len(buttons)} buttons on page:")
            for idx, btn in enumerate(buttons):
                if '+' in btn['text'] or 'Record' in btn['text'] or '记录' in btn['text']:
                    print(f"[{idx}] Text: {btn['text']}, Class: {btn['className']}, HTML: {btn['html']}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
